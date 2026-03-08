<template>
  <div v-if="order">
    <div class="breadcrumb">
      <router-link to="/my-orders">我的订单</router-link> / 订单 #{{ order.id }}
    </div>

    <div class="card">
      <div class="order-header">
        <h1>订单 #{{ order.id }}</h1>
        <span class="order-status" :class="order.status.toLowerCase()">
          {{ statusText(order.status) }}
        </span>
      </div>

      <div class="section">
        <h3>商品明细</h3>
        <div class="items">
          <div class="item-row" v-for="(item, index) in order.items" :key="index">
            <span class="item-name">商品 #{{ item.productId }}</span>
            <span class="item-qty">x{{ item.quantity }}</span>
            <span class="item-price">¥{{ item.price }}</span>
          </div>
        </div>
      </div>

      <div class="order-total">
        <span>订单总额：</span>
        <span class="total-amount">¥{{ order.totalAmount }}</span>
      </div>

      <div class="section" v-if="payment">
        <h3>支付信息</h3>
        <p>支付方式：{{ payment.paymentMethod || '在线支付' }}</p>
        <p>支付状态：{{ payment.status }}</p>
        <p>支付金额：¥{{ payment.amount }}</p>
      </div>
    </div>
  </div>
  <div v-else class="loading">加载中...</div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { orderService, paymentService } from '@/services/apiService'
import type { Order, Payment } from '@/types'

const props = defineProps<{ id: string }>()

const order = ref<Order | null>(null)
const payment = ref<Payment | null>(null)

const statusText = (status: string): string => {
  const map: Record<string, string> = {
    PENDING: '待付款',
    PAID: '已付款',
    SHIPPED: '已发货',
    DELIVERED: '已送达',
    CANCELLED: '已取消',
  }
  return map[status] || status
}

onMounted(async () => {
  try {
    order.value = await orderService.getOrderById(Number(props.id))
    try {
      payment.value = await paymentService.getPaymentByOrderId(Number(props.id))
    } catch {
      // 可能没有支付记录
    }
  } catch (error) {
    console.error('Failed to fetch order', error)
  }
})
</script>

<style scoped>
.breadcrumb {
  margin-bottom: 1rem;
  color: #888;
}

.breadcrumb a { color: #e94560; }

.order-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.order-header h1 { margin: 0; }

.order-status {
  padding: 0.3rem 1rem;
  border-radius: 12px;
  font-size: 0.9rem;
  color: #fff;
}

.order-status.pending { background-color: #f0ad4e; }
.order-status.paid { background-color: #5bc0de; }
.order-status.shipped { background-color: #0275d8; }
.order-status.delivered { background-color: #5cb85c; }
.order-status.cancelled { background-color: #d9534f; }

.section {
  margin-bottom: 1.5rem;
}

.section h3 {
  margin-bottom: 0.75rem;
  color: #555;
}

.item-row {
  display: flex;
  justify-content: space-between;
  padding: 0.5rem 0;
  border-bottom: 1px solid #f0f0f0;
}

.item-name { flex: 1; }
.item-qty { width: 60px; text-align: center; color: #888; }
.item-price { width: 100px; text-align: right; font-weight: bold; }

.order-total {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  padding: 1rem 0;
  border-top: 2px solid #eee;
  margin-bottom: 1.5rem;
}

.total-amount {
  font-size: 1.3rem;
  color: #e94560;
  font-weight: bold;
}

.loading {
  text-align: center;
  padding: 3rem;
  color: #999;
}
</style>
