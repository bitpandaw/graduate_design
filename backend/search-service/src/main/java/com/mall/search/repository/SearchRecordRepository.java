package com.mall.search.repository;

import com.mall.search.model.SearchRecord;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.util.List;

public interface SearchRecordRepository extends JpaRepository<SearchRecord, Long> {

    List<SearchRecord> findByUserIdOrderByCreatedAtDesc(Long userId);

    @Query("SELECT s.keyword, COUNT(s) FROM SearchRecord s GROUP BY s.keyword ORDER BY COUNT(s) DESC")
    List<Object[]> findHotKeywords();
}
