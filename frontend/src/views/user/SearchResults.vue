<template>
  <div>
    <h1>搜索商品</h1>

    <div class="search-bar">
      <input
        v-model="query"
        placeholder="输入关键词搜索..."
        @keyup.enter="doSearch"
      />
      <button class="btn btn-primary" @click="doSearch">搜索</button>
    </div>

    <div class="filters">
      <select v-model="categoryFilter" @change="doSearch">
        <option value="">全部分类</option>
        <option value="ELECTRONICS">电子产品</option>
        <option value="CLOTHING">服装</option>
        <option value="HOME_GOODS">家居</option>
        <option value="BOOKS">图书</option>
        <option value="SPORTS">运动</option>
      </select>
    </div>

    <p class="result-count" v-if="searched">找到 {{ results.length }} 个结果</p>

    <div class="grid" v-if="results.length">
      <div class="card" v-for="product in results" :key="product.id">
        <h3>{{ product.name }}</h3>
        <p class="price">¥{{ product.price }}</p>
        <p class="category">{{ product.category }}</p>
        <p>{{ product.description }}</p>
        <router-link :to="`/products/${product.id}`" class="btn btn-primary">查看详情</router-link>
      </div>
    </div>
    <p v-else-if="searched" class="empty">未找到相关商品</p>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { productService } from '@/services/apiService'
import type { Product } from '@/types'

const route = useRoute()
const query = ref((route.query.q as string) || '')
const categoryFilter = ref('')
const results = ref<Product[]>([])
const searched = ref(false)

const doSearch = async () => {
  if (!query.value.trim() && !categoryFilter.value) return
  searched.value = true
  try {
    if (categoryFilter.value && !query.value.trim()) {
      results.value = await productService.getProductsByCategory(categoryFilter.value)
    } else {
      results.value = await productService.searchProducts(query.value)
      if (categoryFilter.value) {
        results.value = results.value.filter(p => p.category === categoryFilter.value)
      }
    }
  } catch (error) {
    console.error('Search failed', error)
  }
}

onMounted(() => {
  if (query.value) doSearch()
})
</script>

<style scoped>
h1 { margin-bottom: 1.5rem; }

.search-bar {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.search-bar input {
  flex: 1;
  padding: 0.5rem 1rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

.filters {
  margin-bottom: 1rem;
}

.filters select {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.result-count {
  color: #888;
  margin-bottom: 1rem;
}

.price {
  font-size: 1.25rem;
  color: #e94560;
  font-weight: bold;
  margin: 0.5rem 0;
}

.category {
  display: inline-block;
  background: #eef;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-size: 0.85rem;
  margin-bottom: 0.5rem;
}

.empty {
  text-align: center;
  color: #999;
  padding: 3rem 0;
}
</style>
