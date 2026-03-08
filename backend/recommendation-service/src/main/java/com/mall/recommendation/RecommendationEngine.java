package com.mall.recommendation;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.mall.recommendation.model.UserBehavior;
import com.mall.recommendation.repository.UserBehaviorRepository;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.stream.Collectors;
import java.util.stream.IntStream;

/**
 * SASRec 推荐引擎
 *
 * 调用 Python FastAPI 推理服务（端口 8090），实现：
 *   - 基于用户行为序列的 next-item 预测
 *   - 传入 recentItemIds（用户最近行为按时间升序）
 *
 * 推理延迟目标：< 200ms
 * 降级策略：Python 服务不可用时，回退到热度排序（冷启动）
 */
@Slf4j
@Service
public class RecommendationEngine {

    private static final int MAX_SEQ_LEN = 50;

    @Value("${recommendation.python.url:http://localhost:8090}")
    private String pythonServiceUrl;

    @Value("${recommendation.candidate.pool:50}")
    private int candidatePoolSize;

    private final RestTemplate restTemplate = new RestTemplate();
    private final ObjectMapper objectMapper = new ObjectMapper();

    private final UserBehaviorRepository userBehaviorRepository;

    public RecommendationEngine(UserBehaviorRepository userBehaviorRepository) {
        this.userBehaviorRepository = userBehaviorRepository;
    }

    /**
     * 获取用户个性化推荐商品 ID 列表（按 SASRec 分数降序）
     *
     * @param userId 用户 ID
     * @param limit  返回商品数量
     * @return 商品 ID 列表（降序排列）
     */
    public List<Long> recommend(Long userId, int limit) {
        List<Integer> candidateIds = generateCandidatePool(candidatePoolSize);
        try {
            return callPythonService(userId, candidateIds, limit);
        } catch (RestClientException e) {
            log.warn("SASRec 推理服务不可用，降级到热度排序. cause={}", e.getMessage());
            return fallbackRecommend(limit);
        } catch (Exception e) {
            log.error("推荐服务异常", e);
            return fallbackRecommend(limit);
        }
    }

    /**
     * 获取推荐结果（含 SASRec 分数）
     */
    public List<ProductScore> recommendWithScores(Long userId, List<Integer> candidateIds, int limit) {
        List<Integer> recentItemIds = getRecentItemIds(userId);
        try {
            String url = pythonServiceUrl + "/recommend";

            ObjectNode body = objectMapper.createObjectNode();
            body.put("userId", userId);
            ArrayNode idsNode = body.putArray("candidateProductIds");
            candidateIds.forEach(idsNode::add);
            ArrayNode recentNode = body.putArray("recentItemIds");
            recentItemIds.forEach(recentNode::add);
            body.put("limit", limit);

            String response = restTemplate.postForObject(url, body, String.class);
            JsonNode root = objectMapper.readTree(response);
            JsonNode recs = root.get("recommendations");

            List<ProductScore> result = new ArrayList<>();
            if (recs != null && recs.isArray()) {
                for (JsonNode rec : recs) {
                    result.add(new ProductScore(
                            rec.get("productId").asLong(),
                            rec.get("score").asDouble()
                    ));
                }
            }
            return result;
        } catch (Exception e) {
            log.warn("获取带分数推荐失败", e);
            return fallbackRecommend(limit).stream()
                    .map(id -> new ProductScore(id, 0.5))
                    .collect(Collectors.toList());
        }
    }

    /**
     * 检查 Python 推理服务是否健康
     */
    public boolean isPythonServiceHealthy() {
        try {
            String url = pythonServiceUrl + "/health";
            String response = restTemplate.getForObject(url, String.class);
            JsonNode root = objectMapper.readTree(response);
            return "ok".equals(root.path("status").asText());
        } catch (Exception e) {
            return false;
        }
    }

    // ─── 私有方法 ──────────────────────────────────────────────────

    private List<Integer> getRecentItemIds(Long userId) {
        List<UserBehavior> behaviors = userBehaviorRepository
                .findByUserIdOrderByCreatedAtDesc(userId, PageRequest.of(0, MAX_SEQ_LEN));
        List<Integer> ids = behaviors.stream()
                .map(b -> b.getProductId().intValue())
                .collect(Collectors.toList());
        Collections.reverse(ids);
        return ids;
    }

    private List<Long> callPythonService(Long userId, List<Integer> candidateIds, int limit)
            throws Exception {

        String url = pythonServiceUrl + "/recommend";
        List<Integer> recentItemIds = getRecentItemIds(userId);

        ObjectNode body = objectMapper.createObjectNode();
        body.put("userId", userId);
        ArrayNode idsNode = body.putArray("candidateProductIds");
        candidateIds.forEach(idsNode::add);
        ArrayNode recentNode = body.putArray("recentItemIds");
        recentItemIds.forEach(recentNode::add);
        body.put("limit", limit);

        long t0 = System.currentTimeMillis();
        String response = restTemplate.postForObject(url, body, String.class);
        long latency = System.currentTimeMillis() - t0;

        if (latency > 200) {
            log.warn("SASRec 推理延迟超标: {}ms (目标 <200ms)", latency);
        } else {
            log.debug("SASRec 推理延迟: {}ms", latency);
        }

        JsonNode root = objectMapper.readTree(response);
        JsonNode recs = root.get("recommendations");

        List<Long> ids = new ArrayList<>();
        if (recs != null && recs.isArray()) {
            for (JsonNode rec : recs) {
                ids.add(rec.get("productId").asLong());
            }
        }
        return ids;
    }

    /**
     * 生成候选商品池（简化实现：取商品 ID 1~N）
     * 实际应用中应从 product-service 获取活跃商品列表
     */
    private List<Integer> generateCandidatePool(int size) {
        return IntStream.rangeClosed(1, size)
                .boxed()
                .collect(Collectors.toList());
    }

    /**
     * 冷启动降级：返回热门商品（商品 ID 1~limit）
     */
    private List<Long> fallbackRecommend(int limit) {
        return IntStream.rangeClosed(1, limit)
                .mapToLong(Long::valueOf)
                .boxed()
                .collect(Collectors.toList());
    }

    /**
     * 推荐结果（含 SASRec 分数）
     */
    public record ProductScore(Long productId, double score) {}
}