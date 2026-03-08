package com.mall.search.controller;

import com.mall.search.model.SearchRecord;
import com.mall.search.service.SearchService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/search")
@RequiredArgsConstructor
public class SearchController {

    private final SearchService searchService;

    /**
     * 记录搜索（实际搜索通过 product-service 执行，此处记录行为）
     */
    @PostMapping
    public SearchRecord recordSearch(
            @RequestParam Long userId,
            @RequestParam String keyword,
            @RequestParam(defaultValue = "0") int resultCount) {
        return searchService.recordSearch(userId, keyword, resultCount);
    }

    /**
     * 获取用户搜索历史
     */
    @GetMapping("/history/{userId}")
    public List<SearchRecord> getUserSearchHistory(@PathVariable Long userId) {
        return searchService.getUserSearchHistory(userId);
    }

    /**
     * 获取热门搜索词
     */
    @GetMapping("/hot")
    public List<Object[]> getHotKeywords() {
        return searchService.getHotKeywords();
    }
}
