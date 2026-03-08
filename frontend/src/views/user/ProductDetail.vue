<template>
  <div v-if="product">
    <div class="breadcrumb">
      <router-link to="/products">商品</router-link> / {{ product.name }}
    </div>

    <div class="product-detail card">
      <div class="product-info">
        <h1>{{ product.name }}</h1>
        <p class="price">¥{{ product.price }}</p>
        <p class="category">{{ product.category }}</p>
        <p class="description">{{ product.description }}</p>
        <p class="stock">库存: {{ product.stock }} 件</p>

        <div class="quantity-selector">
          <label>数量：</label>
          <button class="btn" @click="quantity > 1 && quantity--">-</button>
          <span class="qty">{{ quantity }}</span>
          <button class="btn" @click="quantity++">+</button>
        </div>

        <div class="actions">
          <button class="btn btn-primary" @click="handleAddToCart">加入购物车</button>
          <button class="btn btn-buy" @click="handleBuyNow">立即购买</button>
        </div>
      </div>
    </div>
  </div>
  <div v-else class="loading">加载中...</div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { productService, cartService } from '@/services/apiService'
import { useAuth } from '@/composables/useAuth'
import type { Product } from '@/types'

const props = defineProps<{ id: string }>()
const router = useRouter()
const { isLoggedIn } = useAuth()

const product = ref<Product | null>(null)
const quantity = ref(1)

onMounted(async () => {
  try {
    product.value = await productService.getProductById(Number(props.id))
  } catch (error) {
    console.error('Failed to fetch product', error)
  }
})

const handleAddToCart = () => {
  if (!product.value) return
  cartService.addToCart({
    productId: product.value.id,
    productName: product.value.name,
    price: product.value.price,
    quantity: quantity.value,
  })
  alert(`已将 ${product.value.name} x${quantity.value} 加入购物车`)
}

const handleBuyNow = () => {
  if (!isLoggedIn.value) {
    router.push({ name: 'Login', query: { redirect: `/products/${props.id}` } })
    return
  }
  handleAddToCart()
  router.push('/cart')
}
</script>

<style scoped>
.breadcrumb {
  margin-bottom: 1rem;
  color: #888;
}

.breadcrumb a {
  color: #e94560;
}

.product-detail {
  padding: 2rem;
}

h1 {
  margin-bottom: 1rem;
}

.price {
  font-size: 2rem;
  color: #e94560;
  font-weight: bold;
  margin-bottom: 1rem;
}

.category {
  display: inline-block;
  background: #eef;
  padding: 0.3rem 0.75rem;
  border-radius: 4px;
  font-size: 0.9rem;
  margin-bottom: 1rem;
}

.description {
  color: #555;
  line-height: 1.8;
  margin-bottom: 1rem;
}

.stock {
  color: #888;
  margin-bottom: 1.5rem;
}

.quantity-selector {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}

.quantity-selector .btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #eee;
}

.qty {
  font-size: 1.1rem;
  min-width: 2rem;
  text-align: center;
}

.actions {
  display: flex;
  gap: 1rem;
}

.btn-buy {
  background: #ff6b35;
  color: #fff;
}

.btn-buy:hover {
  background: #e55a2b;
}

.loading {
  text-align: center;
  padding: 3rem;
  color: #999;
}
</style>
