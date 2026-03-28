package com.mall.user;

import jakarta.persistence.*;
import lombok.Data;
import java.math.BigDecimal;

@Data
@Entity
@Table(name = "users")
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(unique = true)
    private String username;

    private String email;
    private String passwordHash;

    @Enumerated(EnumType.STRING)
    private UserLevel level;

    private BigDecimal balance;

    @Enumerated(EnumType.STRING)
    private Role role;

    public enum UserLevel {
        BRONZE, SILVER, GOLD, PLATINUM
    }

    public enum Role {
        USER, ADMIN
    }
}