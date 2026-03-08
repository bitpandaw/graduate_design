<template>
  <div>
    <h1>确认订单</h1>

    <div v-if="cartItems.length">
      <div class="card">
        <h2>商品清单</h2>
        <div class="order-items">
          <div class="order-item" v-for="item in cartItems" :key="item.productId">
            <span class="item-name">{{ item.productName }}</span>
            <span class="item-qty">x{{ item.quantity }}</span>
            <span class="item-price">¥{{ (item.price * item.quantity).toFixed(2) }}</span>
          </div>
        </div>
        <div class="order-total">
          <span>订单总额：</span>
          <span class="total-price">¥{{ total.toFixed(2) }}</span>
        </div>
      </div>

      <div class="card">
        <h2>支付方式</h2>
        <div class="payment-methods">
          <label v-for="method in paymentMethods" :key="method.value">
            <input type="radio" v-model="paymentMethod" :value="method.value" />
            {{ method.label }}
          </label>
        </div>
      </div>

      <div class="actions">
        <router-link to="/cart" class="btn">返回购物车</router-link>
        <button class="btn btn-primary" @click="submitOrder" :disabled="submitting">
          {{ submitting ? '提交中...' : '提交订单' }}
        </button>
      </div>
    </div>

    <div v-else class="empty">
      <p>购物车为空，无法结算</p>
      <router-link to="/products" class="btn btn-primary">去购物</router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { cartService, orderService, paymentService } from '@/services/apiService'
import { useAuth } from '@/composables/useAuth'
import type { CartItem } from '@/types'

const router = useRouter()
const { userId } = useAuth()
const cartItems = ref<CartItem[]>(cartService.getCart())
const paymentMethod = ref('ALIPAY')
const submitting = ref(false)

const paymentMethods = [
  { label: '支付宝', value: 'ALIPAY' },
  { label: '微信支付', value: 'WECHAT' },
  { label: '银行卡', value: 'BANK_CARD' },
]

const total = computed(() =>
  cartItems.value.reduce((sum, item) => sum + item.price * item.quantity, 0)
)

const submitOrder = async () => {
  if (submitting.value) return
  submitting.value = true

  try {
    const order = await orderService.createOrder({
      userId: userId.value,
      totalAmount: total.value,
      items: cartItems.value.map(item => ({
        productId: item.productId,
        quantity: item.quantity,
        price: item.price,
      })),
    })

    await paymentService.createPayment({
      orderId: order.id,
      amount: total.value,
      paymentMethod: paymentMethod.value,
    })

    cartService.clearCart()
    alert('订单提交成功！')
    router.push('/my-orders')
  } catch (error) {
    console.error('Failed to submit order', error)
    alert('订单提交失败，请重试')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
h1 { margin-bottom: 1.5rem; }
h2 { margin-bottom: 1rem; font-size: 1.2rem; }

.order-items {
  margin-bottom: 1rem;
}

.order-item {
  display: flex;
  justify-content: space-between;
  padding: 0.5rem 0;
  border-bottom: 1px solid #f0f0f0;
}

.item-name { flex: 1; }
.item-qty { color: #888; width: 60px; text-align: center; }
.item-price { font-weight: bold; width: 100px; text-align: right; }

.order-total {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  padding-top: 1rem;
  font-size: 1.1rem;
}

.total-price {
  color: #e94560;
  font-weight: bold;
  font-size: 1.3rem;
}

.payment-methods {
  display: flex;
  gap: 1.5rem;
}

.payment-methods label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

.actions {
  display: flex;
  justify-content: space-between;
  margin-top: 1.5rem;
}

.actions .btn:first-child {
  background: #eee;
  color: #666;
}

.empty {
  text-align: center;
  padding: 3rem;
  color: #999;
}
</style>
