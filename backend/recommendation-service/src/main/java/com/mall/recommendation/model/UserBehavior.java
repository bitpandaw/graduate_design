package com.mall.recommendation.model;

import jakarta.persistence.*;
import lombok.Data;
import java.time.LocalDateTime;

/**
 * 用户行为记录实体，用于推荐算法的特征收集。
 * 记录用户对商品的浏览、点击、购买等行为。
 */
@Data
@Entity
@Table(name = "user_behaviors")
public class UserBehavior {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private Long userId;
    private Long productId;

    @Enumerated(EnumType.STRING)
    private BehaviorType behaviorType;

    private LocalDateTime createdAt;

    public enum BehaviorType {
        VIEW, CLICK, ADD_CART, PURCHASE, RATE
    }
}
