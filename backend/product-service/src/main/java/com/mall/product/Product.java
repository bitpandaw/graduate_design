package com.mall.product;

import jakarta.persistence.*;
import lombok.Data;
import java.math.BigDecimal;

@Data
@Entity
@Table(name = "products")
public class Product {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String name;
    private BigDecimal price;
    private Integer stock;

    @Enumerated(EnumType.STRING)
    private Category category;

    private String description;

    public enum Category {
        ELECTRONICS, CLOTHING, HOME_GOODS, BOOKS, SPORTS
    }
}