<template>
  <div>
    <h1>商品浏览</h1>

    <div class="toolbar">
      <div class="search-bar">
        <input
          v-model="searchKeyword"
          placeholder="搜索商品..."
          @keyup.enter="handleSearch"
        />
        <button class="btn btn-primary" @click="handleSearch">搜索</button>
      </div>
      <div class="category-filter">
        <button
          v-for="cat in categories"
          :key="cat.value"
          class="btn"
          :class="{ 'btn-primary': selectedCategory === cat.value }"
          @click="filterByCategory(cat.value)"
        >
          {{ cat.label }}
        </button>
      </div>
    </div>

    <div class="grid" v-if="products.length">
      <div class="card product-card" v-for="product in products" :key="product.id">
        <h3>{{ product.name }}</h3>
        <p class="price">¥{{ product.price }}</p>
        <p class="category">{{ product.category }}</p>
        <p class="desc">{{ product.description }}</p>
        <p class="stock">库存: {{ product.stock }}</p>
        <div class="card-actions">
          <router-link :to="`/products/${product.id}`" class="btn btn-primary">查看详情</router-link>
          <button class="btn btn-cart" @click="handleAddToCart(product)">加入购物车</button>
        </div>
      </div>
    </div>
    <p v-else class="empty">暂无商品数据</p>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { productService, cartService } from '@/services/apiService'
import type { Product } from '@/types'

const products = ref<Product[]>([])
const searchKeyword = ref('')
const selectedCategory = ref('')

const categories = [
  { label: '全部', value: '' },
  { label: '电子产品', value: 'ELECTRONICS' },
  { label: '服装', value: 'CLOTHING' },
  { label: '家居', value: 'HOME_GOODS' },
  { label: '图书', value: 'BOOKS' },
  { label: '运动', value: 'SPORTS' },
]

const fetchProducts = async () => {
  try {
    products.value = await productService.getProducts()
  } catch (error) {
    console.error('Failed to fetch products', error)
  }
}

const handleSearch = async () => {
  selectedCategory.value = ''
  if (!searchKeyword.value.trim()) {
    await fetchProducts()
    return
  }
  try {
    products.value = await productService.searchProducts(searchKeyword.value)
  } catch (error) {
    console.error('Search failed', error)
  }
}

const filterByCategory = async (category: string) => {
  selectedCategory.value = category
  searchKeyword.value = ''
  if (!category) {
    await fetchProducts()
    return
  }
  try {
    products.value = await productService.getProductsByCategory(category)
  } catch (error) {
    console.error('Failed to filter by category', error)
  }
}

const handleAddToCart = (product: Product) => {
  cartService.addToCart({
    productId: product.id,
    productName: product.name,
    price: product.price,
    quantity: 1,
  })
  alert(`已将 ${product.name} 加入购物车`)
}

onMounted(fetchProducts)
</script>

<style scoped>
h1 {
  margin-bottom: 1.5rem;
}

.toolbar {
  margin-bottom: 1.5rem;
}

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

.category-filter {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.category-filter .btn {
  background: #eee;
  color: #333;
}

.category-filter .btn.btn-primary {
  background: #e94560;
  color: #fff;
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

.desc {
  color: #666;
  font-size: 0.9rem;
  flex: 1;
}

.stock {
  color: #888;
  font-size: 0.85rem;
  margin-top: 0.5rem;
}

.product-card {
  display: flex;
  flex-direction: column;
}

.card-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 1rem;
}

.btn-cart {
  background: #16213e;
  color: #fff;
}

.btn-cart:hover {
  background: #1a1a2e;
}

.empty {
  text-align: center;
  color: #999;
  padding: 3rem 0;
}
</style>
