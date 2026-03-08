package com.mall.recommendation.controller;

import com.mall.recommendation.RecommendationEngine;
import com.mall.recommendation.model.UserBehavior;
import com.mall.recommendation.repository.UserBehaviorRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * 推荐服务 Controller（论文第4章：推荐服务模块实现）
 */
@RestController
@RequestMapping("/api/recommendations")
@RequiredArgsConstructor
public class RecommendationController {

    private final RecommendationEngine recommendationEngine;
    private final UserBehaviorRepository userBehaviorRepository;

    /**
     * 获取用户个性化推荐商品 ID 列表（SASRec 降序排列）
     */
    @GetMapping("/user/{userId}")
    public List<Long> getRecommendations(
            @PathVariable Long userId,
            @RequestParam(defaultValue = "10") int limit) {
        return recommendationEngine.recommend(userId, limit);
    }

    /**
     * 获取推荐结果（含 SASRec 分数，用于前端展示排序依据）
     */
    @GetMapping("/user/{userId}/scored")
    public List<RecommendationEngine.ProductScore> getRecommendationsWithScores(
            @PathVariable Long userId,
            @RequestParam(defaultValue = "10") int limit,
            @RequestParam(defaultValue = "") List<Integer> candidates) {
        if (candidates.isEmpty()) {
            // 未传候选集时，使用前 50 个商品作为候选池
            candidates = new java.util.ArrayList<>();
            for (int i = 1; i <= 50; i++) candidates.add(i);
        }
        return recommendationEngine.recommendWithScores(userId, candidates, limit);
    }

    /**
     * 记录用户行为（用于推荐算法的特征收集）
     * 行为权重：VIEW=1, CLICK=2, ADD_CART=3, RATE=4, PURCHASE=5
     */
    @PostMapping("/behavior")
    public UserBehavior recordBehavior(@RequestBody UserBehavior behavior) {
        behavior.setCreatedAt(LocalDateTime.now());
        return userBehaviorRepository.save(behavior);
    }

    /**
     * 获取用户行为历史
     */
    @GetMapping("/behavior/{userId}")
    public List<UserBehavior> getUserBehaviors(@PathVariable Long userId) {
        return userBehaviorRepository.findByUserId(userId);
    }

    /**
     * 导出全部行为数据（供 SASRec 训练使用，含 createdAt）
     */
    @GetMapping("/export/behaviors")
    public List<Map<String, Object>> exportBehaviors() {
        List<UserBehavior> all = userBehaviorRepository.findAll();
        DateTimeFormatter fmt = DateTimeFormatter.ISO_LOCAL_DATE_TIME;
        return all.stream().map(b -> {
            Map<String, Object> m = new HashMap<>();
            m.put("userId", b.getUserId());
            m.put("productId", b.getProductId());
            m.put("behaviorType", b.getBehaviorType() != null ? b.getBehaviorType().name() : "VIEW");
            m.put("createdAt", b.getCreatedAt() != null ? b.getCreatedAt().format(fmt) : "");
            return m;
        }).collect(Collectors.toList());
    }

    /**
     * 检查 Python SASRec 推理服务状态
     */
    @GetMapping("/status")
    public ResponseEntity<Map<String, Object>> serviceStatus() {
        boolean healthy = recommendationEngine.isPythonServiceHealthy();
        return ResponseEntity.ok(Map.of(
                "pythonService", healthy ? "UP" : "DOWN",
                "mode", healthy ? "sasrec" : "cold_start_fallback",
                "description", healthy
                        ? "SASRec 模型推理服务正常运行"
                        : "Python 推理服务不可用，使用冷启动降级策略"
        ));
    }
}
