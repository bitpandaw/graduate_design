<template>
  <div>
    <section class="hero">
      <h1>电商推荐系统</h1>
      <p>基于 Wide & Deep 推荐模型的智能电商平台</p>
      <router-link to="/products" class="btn btn-primary hero-btn">浏览商品</router-link>
    </section>

    <section class="features">
      <div class="grid">
        <div class="card">
          <h3>智能推荐</h3>
          <p>基于用户行为和商品特征，为您提供个性化的商品推荐。</p>
        </div>
        <div class="card">
          <h3>丰富品类</h3>
          <p>涵盖电子产品、服装、家居、图书、运动等多个品类。</p>
        </div>
        <div class="card">
          <h3>订单跟踪</h3>
          <p>完整的订单生命周期管理，从下单到配送全程可追踪。</p>
        </div>
      </div>
    </section>

    <section class="recommended" v-if="recommendedProducts.length">
      <h2>为您推荐</h2>
      <div class="grid">
        <div class="card product-card" v-for="product in recommendedProducts" :key="product.id">
          <h3>{{ product.name }}</h3>
          <p class="price">¥{{ product.price }}</p>
          <p class="category">{{ product.category }}</p>
          <p>{{ product.description }}</p>
          <router-link :to="`/products/${product.id}`" class="btn btn-primary">查看详情</router-link>
        </div>
      </div>
    </section>

    <section class="hot-products">
      <h2>热门商品</h2>
      <div class="grid">
        <div class="card product-card" v-for="product in hotProducts" :key="product.id">
          <h3>{{ product.name }}</h3>
          <p class="price">¥{{ product.price }}</p>
          <p class="category">{{ product.category }}</p>
          <p>{{ product.description }}</p>
          <router-link :to="`/products/${product.id}`" class="btn btn-primary">查看详情</router-link>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { productService, recommendationService } from '@/services/apiService'
import { useAuth } from '@/composables/useAuth'
import type { Product } from '@/types'

const { isLoggedIn, userId } = useAuth()
const recommendedProducts = ref<Product[]>([])
const hotProducts = ref<Product[]>([])

onMounted(async () => {
  try {
    const allProducts = await productService.getProducts()
    hotProducts.value = allProducts.slice(0, 6)

    if (isLoggedIn.value) {
      try {
        const recIds = await recommendationService.getRecommendations(userId.value, 4)
        if (Array.isArray(recIds) && recIds.length) {
          const products = await Promise.all(
            recIds.map((id: number) => productService.getProductById(id).catch(() => null))
          )
          recommendedProducts.value = products.filter(Boolean)
        }
      } catch {
        // 推荐服务不可用时静默处理
      }
    }
  } catch (error) {
    console.error('Failed to fetch products', error)
  }
})
</script>

<style scoped>
.hero {
  text-align: center;
  padding: 3rem 1rem;
  background: linear-gradient(135deg, #1a1a2e, #16213e);
  color: #fff;
  border-radius: 8px;
  margin-bottom: 2rem;
}

.hero h1 {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
}

.hero p {
  font-size: 1.1rem;
  color: #ccc;
  margin-bottom: 1.5rem;
}

.hero-btn {
  font-size: 1rem;
  padding: 0.75rem 2rem;
}

.features {
  margin-bottom: 2rem;
}

.features h3 {
  color: #e94560;
  margin-bottom: 0.5rem;
}

section h2 {
  margin-bottom: 1rem;
  font-size: 1.5rem;
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

.product-card {
  display: flex;
  flex-direction: column;
}

.product-card .btn {
  margin-top: auto;
  text-align: center;
}

.hot-products, .recommended {
  margin-top: 2rem;
}
</style>
