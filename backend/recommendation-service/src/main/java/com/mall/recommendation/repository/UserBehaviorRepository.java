package com.mall.recommendation.repository;

import com.mall.recommendation.model.UserBehavior;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface UserBehaviorRepository extends JpaRepository<UserBehavior, Long> {

    List<UserBehavior> findByUserId(Long userId);

    List<UserBehavior> findByUserIdOrderByCreatedAtAsc(Long userId);

    List<UserBehavior> findByUserIdOrderByCreatedAtDesc(Long userId, Pageable pageable);

    List<UserBehavior> findByUserIdAndBehaviorType(Long userId, UserBehavior.BehaviorType behaviorType);

    List<UserBehavior> findByProductId(Long productId);
}
