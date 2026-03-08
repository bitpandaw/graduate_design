package com.mall.order.repository;

import com.mall.order.Order;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface OrderRepository extends JpaRepository<Order, Long> {

    List<Order> findByUserId(Long userId);

    List<Order> findByStatus(Order.Status status);

    List<Order> findByUserIdAndStatus(Long userId, Order.Status status);
}
