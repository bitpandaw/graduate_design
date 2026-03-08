<template>
  <div>
    <h1>我的订单</h1>

    <div v-if="orders.length">
      <div class="card" v-for="order in orders" :key="order.id">
        <div class="order-header">
          <span class="order-id">订单 #{{ order.id }}</span>
          <span class="order-status" :class="order.status.toLowerCase()">
            {{ statusText(order.status) }}
          </span>
        </div>
        <p class="total">总金额: ¥{{ order.totalAmount }}</p>
        <div v-if="order.items && order.items.length">
          <ul>
            <li v-for="(item, index) in order.items" :key="index">
              商品#{{ item.productId }} x {{ item.quantity }} - ¥{{ item.price }}
            </li>
          </ul>
        </div>
        <div class="order-actions">
          <router-link :to="`/my-orders/${order.id}`" class="btn btn-primary">查看详情</router-link>
          <button
            v-if="order.status === 'PENDING'"
            class="btn btn-cancel"
            @click="handleCancel(order.id)"
          >
            取消订单
          </button>
        </div>
      </div>
    </div>
    <p v-else class="empty">暂无订单</p>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { orderService } from '@/services/apiService'
import { useAuth } from '@/composables/useAuth'
import type { Order } from '@/types'

const { userId } = useAuth()
const orders = ref<Order[]>([])

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

const fetchOrders = async () => {
  try {
    if (userId.value) {
      orders.value = await orderService.getOrdersByUserId(userId.value)
    } else {
      orders.value = await orderService.getOrders()
    }
  } catch (error) {
    console.error('Failed to fetch orders', error)
  }
}

const handleCancel = async (orderId: number) => {
  if (!confirm('确定要取消此订单吗？')) return
  try {
    await orderService.cancelOrder(orderId)
    await fetchOrders()
  } catch (error) {
    console.error('Failed to cancel order', error)
    alert('取消失败')
  }
}

onMounted(fetchOrders)
</script>

<style scoped>
h1 { margin-bottom: 1.5rem; }

.order-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.order-id {
  font-weight: bold;
  font-size: 1.1rem;
}

.order-status {
  padding: 0.2rem 0.75rem;
  border-radius: 12px;
  font-size: 0.85rem;
  color: #fff;
}

.order-status.pending { background-color: #f0ad4e; }
.order-status.paid { background-color: #5bc0de; }
.order-status.shipped { background-color: #0275d8; }
.order-status.delivered { background-color: #5cb85c; }
.order-status.cancelled { background-color: #d9534f; }

.total {
  font-size: 1.1rem;
  color: #e94560;
  font-weight: bold;
  margin: 0.5rem 0;
}

ul {
  padding-left: 1.5rem;
  margin-top: 0.5rem;
}

.order-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 1rem;
}

.btn-cancel {
  background: #f0f0f0;
  color: #d9534f;
}

.btn-cancel:hover {
  background: #d9534f;
  color: #fff;
}

.empty {
  text-align: center;
  color: #999;
  padding: 3rem 0;
}
</style>
