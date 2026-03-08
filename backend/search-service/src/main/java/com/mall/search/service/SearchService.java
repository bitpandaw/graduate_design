package com.mall.search.service;

import com.mall.search.model.SearchRecord;
import com.mall.search.repository.SearchRecordRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;

@Service
@RequiredArgsConstructor
public class SearchService {

    private final SearchRecordRepository searchRecordRepository;

    /**
     * 记录用户搜索行为
     */
    public SearchRecord recordSearch(Long userId, String keyword, int resultCount) {
        SearchRecord record = new SearchRecord();
        record.setUserId(userId);
        record.setKeyword(keyword);
        record.setResultCount(resultCount);
        record.setCreatedAt(LocalDateTime.now());
        return searchRecordRepository.save(record);
    }

    /**
     * 获取用户搜索历史
     */
    public List<SearchRecord> getUserSearchHistory(Long userId) {
        return searchRecordRepository.findByUserIdOrderByCreatedAtDesc(userId);
    }

    /**
     * 获取热门搜索关键词
     */
    public List<Object[]> getHotKeywords() {
        return searchRecordRepository.findHotKeywords();
    }
}
