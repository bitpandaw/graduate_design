<template>
  <div v-if="order">
    <div class="breadcrumb">
      <router-link to="/admin/orders">订单管理</router-link> / 订单 #{{ order.id }}
    </div>

    <div class="card">
      <div class="order-header">
        <h2>订单 #{{ order.id }}</h2>
        <span class="status-badge" :class="order.status.toLowerCase()">
          {{ statusText(order.status) }}
        </span>
      </div>

      <div class="info-grid">
        <div class="info-item">
          <label>用户ID</label>
          <p>
            <router-link :to="`/admin/users/${order.userId}`">{{ order.userId }}</router-link>
          </p>
        </div>
        <div class="info-item">
          <label>订单总额</label>
          <p class="amount">¥{{ order.totalAmount }}</p>
        </div>
      </div>

      <h3>商品明细</h3>
      <table class="data-table" v-if="order.items?.length">
        <thead>
          <tr>
            <th>商品ID</th>
            <th>数量</th>
            <th>单价</th>
            <th>小计</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(item, index) in order.items" :key="index">
            <td>{{ item.productId }}</td>
            <td>{{ item.quantity }}</td>
            <td>¥{{ item.price }}</td>
            <td>¥{{ (item.price * item.quantity).toFixed(2) }}</td>
          </tr>
        </tbody>
      </table>

      <div class="status-update" v-if="order.status !== 'CANCELLED' && order.status !== 'DELIVERED'">
        <h3>更新状态</h3>
        <div class="status-actions">
          <select v-model="newStatus">
            <option value="PENDING">待付款</option>
            <option value="PAID">已付款</option>
            <option value="SHIPPED">已发货</option>
            <option value="DELIVERED">已送达</option>
            <option value="CANCELLED">已取消</option>
          </select>
          <button class="btn btn-primary" @click="updateStatus">更新</button>
        </div>
      </div>
    </div>
  </div>
  <div v-else class="loading">加载中...</div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { orderService } from '@/services/apiService'
import type { Order } from '@/types'

const props = defineProps<{ id: string }>()

const order = ref<Order | null>(null)
const newStatus = ref('')

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
    newStatus.value = order.value?.status || ''
  } catch (error) {
    console.error('Failed to fetch order', error)
  }
})

const updateStatus = async () => {
  if (!order.value || !newStatus.value) return
  try {
    await orderService.updateOrderStatus(order.value.id, newStatus.value)
    order.value = await orderService.getOrderById(Number(props.id))
    alert('状态更新成功')
  } catch (error) {
    console.error('Failed to update status', error)
    alert('更新失败')
  }
}
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

.status-badge {
  padding: 0.3rem 1rem;
  border-radius: 12px;
  font-size: 0.9rem;
  color: #fff;
}

.status-badge.pending { background-color: #f0ad4e; }
.status-badge.paid { background-color: #5bc0de; }
.status-badge.shipped { background-color: #0275d8; }
.status-badge.delivered { background-color: #5cb85c; }
.status-badge.cancelled { background-color: #d9534f; }

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.info-item label {
  display: block;
  color: #888;
  font-size: 0.85rem;
  margin-bottom: 0.25rem;
}

.info-item a { color: #e94560; }

.amount {
  color: #e94560;
  font-weight: bold;
  font-size: 1.2rem;
}

h3 { margin-bottom: 0.75rem; margin-top: 1rem; }

.data-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 1.5rem;
}

.data-table th,
.data-table td {
  padding: 0.75rem 1rem;
  text-align: left;
  border-bottom: 1px solid #f0f0f0;
}

.data-table th {
  font-weight: 600;
  color: #555;
}

.status-update {
  border-top: 1px solid #eee;
  padding-top: 1rem;
}

.status-actions {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.status-actions select {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.loading {
  text-align: center;
  padding: 3rem;
  color: #999;
}
</style>
