package com.mall.order;

import jakarta.persistence.*;
import lombok.Data;
import java.math.BigDecimal;
import java.util.List;

@Data
@Entity
@Table(name = "orders")
public class Order {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private Long userId;
    private BigDecimal totalAmount;

    @Enumerated(EnumType.STRING)
    private Status status;

    @ElementCollection
    private List<OrderItem> items;

    public enum Status {
        PENDING, PAID, SHIPPED, DELIVERED, CANCELLED
    }

    @Embeddable
    @Data
    public static class OrderItem {
        private Long productId;
        private Integer quantity;
        private BigDecimal price;
    }
}