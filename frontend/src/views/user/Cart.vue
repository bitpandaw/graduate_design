<template>
  <div>
    <h1>购物车</h1>

    <div v-if="cartItems.length">
      <div class="card cart-item" v-for="item in cartItems" :key="item.productId">
        <div class="item-info">
          <h3>{{ item.productName }}</h3>
          <p class="price">¥{{ item.price }}</p>
        </div>
        <div class="item-quantity">
          <button class="btn" @click="updateQty(item.productId, item.quantity - 1)">-</button>
          <span class="qty">{{ item.quantity }}</span>
          <button class="btn" @click="updateQty(item.productId, item.quantity + 1)">+</button>
        </div>
        <div class="item-subtotal">
          ¥{{ (item.price * item.quantity).toFixed(2) }}
        </div>
        <button class="btn btn-remove" @click="removeItem(item.productId)">删除</button>
      </div>

      <div class="cart-footer card">
        <div class="cart-total">
          <span>共 {{ totalCount }} 件商品</span>
          <span class="total-price">合计：¥{{ total.toFixed(2) }}</span>
        </div>
        <div class="cart-actions">
          <button class="btn" @click="clearAll">清空购物车</button>
          <router-link to="/checkout" class="btn btn-primary">去结算</router-link>
        </div>
      </div>
    </div>

    <div v-else class="empty">
      <p>购物车是空的</p>
      <router-link to="/products" class="btn btn-primary">去逛逛</router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { cartService } from '@/services/apiService'
import type { CartItem } from '@/types'

const cartItems = ref<CartItem[]>(cartService.getCart())

const total = computed(() =>
  cartItems.value.reduce((sum, item) => sum + item.price * item.quantity, 0)
)

const totalCount = computed(() =>
  cartItems.value.reduce((sum, item) => sum + item.quantity, 0)
)

const updateQty = (productId: number, quantity: number) => {
  if (quantity <= 0) {
    removeItem(productId)
    return
  }
  cartItems.value = cartService.updateQuantity(productId, quantity)
}

const removeItem = (productId: number) => {
  cartItems.value = cartService.removeFromCart(productId)
}

const clearAll = () => {
  cartItems.value = cartService.clearCart()
}
</script>

<style scoped>
h1 { margin-bottom: 1.5rem; }

.cart-item {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  padding: 1rem 1.5rem;
}

.item-info {
  flex: 1;
}

.item-info h3 {
  margin-bottom: 0.25rem;
}

.price {
  color: #888;
}

.item-quantity {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.item-quantity .btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #eee;
  padding: 0;
}

.qty {
  min-width: 2rem;
  text-align: center;
}

.item-subtotal {
  font-size: 1.1rem;
  font-weight: bold;
  color: #e94560;
  min-width: 80px;
  text-align: right;
}

.btn-remove {
  background: none;
  color: #999;
  font-size: 0.85rem;
}

.btn-remove:hover {
  color: #e94560;
}

.cart-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.25rem 1.5rem;
  margin-top: 1rem;
}

.total-price {
  font-size: 1.25rem;
  font-weight: bold;
  color: #e94560;
  margin-left: 1.5rem;
}

.cart-actions {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.cart-actions .btn:first-child {
  background: #eee;
  color: #666;
}

.empty {
  text-align: center;
  padding: 3rem;
  color: #999;
}

.empty .btn {
  margin-top: 1rem;
}
</style>
