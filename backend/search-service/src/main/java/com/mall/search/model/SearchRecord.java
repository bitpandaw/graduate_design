package com.mall.search.model;

import jakarta.persistence.*;
import lombok.Data;
import java.time.LocalDateTime;

/**
 * 搜索记录实体，记录用户搜索历史
 */
@Data
@Entity
@Table(name = "search_records")
public class SearchRecord {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private Long userId;
    private String keyword;
    private Integer resultCount;
    private LocalDateTime createdAt;
}
