package com.mall.order.service;

import com.mall.order.Order;
import com.mall.order.repository.OrderRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class OrderService {

    private final OrderRepository orderRepository;

    public List<Order> getAllOrders() {
        return orderRepository.findAll();
    }

    public Optional<Order> getOrderById(Long id) {
        return orderRepository.findById(id);
    }

    public List<Order> getOrdersByUserId(Long userId) {
        return orderRepository.findByUserId(userId);
    }

    public Order createOrder(Order order) {
        order.setStatus(Order.Status.PENDING);
        return orderRepository.save(order);
    }

    public Optional<Order> updateOrderStatus(Long id, Order.Status status) {
        return orderRepository.findById(id).map(order -> {
            order.setStatus(status);
            return orderRepository.save(order);
        });
    }

    public Optional<Order> cancelOrder(Long id) {
        return updateOrderStatus(id, Order.Status.CANCELLED);
    }
}
