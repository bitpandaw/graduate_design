package com.mall.recommendation;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;
import java.util.stream.IntStream;

/**
 * Wide & Deep 推荐引擎（论文第3-4章实现）
 *
 * 调用 Python FastAPI 推理服务（端口 8090），实现：
 *   - Wide 部分：user_id × category 特征交叉（记忆能力）
 *   - Deep 部分：Embedding → MLP（泛化能力）
 *   - K-means 商品聚类 ClusterID 特征融合
 *
 * 推理延迟目标：< 200ms（论文非功能需求）
 * 降级策略：Python 服务不可用时，回退到热度排序（冷启动）
 */
@Slf4j
@Service
public class RecommendationEngine {

    @Value("${recommendation.python.url:http://localhost:8090}")
    private String pythonServiceUrl;

    @Value("${recommendation.candidate.pool:50}")
    private int candidatePoolSize;

    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper;

    public RecommendationEngine() {
        this.restTemplate = new RestTemplate();
        this.objectMapper = new ObjectMapper();
    }

    /**
     * 获取用户个性化推荐商品 ID 列表（按 Wide & Deep 分数降序）
     *
     * @param userId 用户 ID
     * @param limit  返回商品数量
     * @return 商品 ID 列表（降序排列）
     */
    public List<Long> recommend(Long userId, int limit) {
        // 生成候选商品池（实际应从商品库过滤，此处取前 N 个商品 ID）
        List<Integer> candidateIds = generateCandidatePool(candidatePoolSize);

        try {
            return callPythonService(userId, candidateIds, limit);
        } catch (RestClientException e) {
            log.warn("Wide & Deep 推理服务不可用，降级到热度排序. cause={}", e.getMessage());
            return fallbackRecommend(limit);
        } catch (Exception e) {
            log.error("推荐服务异常", e);
            return fallbackRecommend(limit);
        }
    }

    /**
     * 获取推荐结果（含分数）
     */
    public List<ProductScore> recommendWithScores(Long userId, List<Integer> candidateIds, int limit) {
        try {
            String url = pythonServiceUrl + "/recommend";

            ObjectNode body = objectMapper.createObjectNode();
            body.put("userId", userId);
            ArrayNode idsNode = body.putArray("candidateProductIds");
            candidateIds.forEach(idsNode::add);
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

    private List<Long> callPythonService(Long userId, List<Integer> candidateIds, int limit)
            throws Exception {

        String url = pythonServiceUrl + "/recommend";

        ObjectNode body = objectMapper.createObjectNode();
        body.put("userId", userId);
        ArrayNode idsNode = body.putArray("candidateProductIds");
        candidateIds.forEach(idsNode::add);
        body.put("limit", limit);

        long t0 = System.currentTimeMillis();
        String response = restTemplate.postForObject(url, body, String.class);
        long latency = System.currentTimeMillis() - t0;

        if (latency > 200) {
            log.warn("Wide & Deep 推理延迟超标: {}ms (目标 <200ms)", latency);
        } else {
            log.debug("Wide & Deep 推理延迟: {}ms", latency);
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
     * 推荐结果（含 Wide & Deep 分数）
     */
    public record ProductScore(Long productId, double score) {}
}