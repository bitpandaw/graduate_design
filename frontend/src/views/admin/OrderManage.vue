<template>
  <div>
    <div class="toolbar">
      <div class="filter-group">
        <select v-model="statusFilter">
          <option value="">全部状态</option>
          <option value="PENDING">待付款</option>
          <option value="PAID">已付款</option>
          <option value="SHIPPED">已发货</option>
          <option value="DELIVERED">已送达</option>
          <option value="CANCELLED">已取消</option>
        </select>
      </div>
      <span class="count">共 {{ filteredOrders.length }} 个订单</span>
    </div>

    <div class="card">
      <table class="data-table">
        <thead>
          <tr>
            <th>订单ID</th>
            <th>用户ID</th>
            <th>金额</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="order in filteredOrders" :key="order.id">
            <td>
              <router-link :to="`/admin/orders/${order.id}`">#{{ order.id }}</router-link>
            </td>
            <td>
              <router-link :to="`/admin/users/${order.userId}`">用户#{{ order.userId }}</router-link>
            </td>
            <td class="amount">¥{{ order.totalAmount }}</td>
            <td>
              <span class="status-badge" :class="order.status.toLowerCase()">
                {{ statusText(order.status) }}
              </span>
            </td>
            <td>
              <router-link :to="`/admin/orders/${order.id}`" class="btn btn-sm">详情</router-link>
              <select
                v-if="order.status !== 'CANCELLED' && order.status !== 'DELIVERED'"
                class="status-select"
                :value="order.status"
                @change="handleStatusChange(order.id, ($event.target as HTMLSelectElement).value)"
              >
                <option value="PENDING">待付款</option>
                <option value="PAID">已付款</option>
                <option value="SHIPPED">已发货</option>
                <option value="DELIVERED">已送达</option>
                <option value="CANCELLED">已取消</option>
              </select>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { orderService } from '@/services/apiService'
import type { Order } from '@/types'

const orders = ref<Order[]>([])
const statusFilter = ref('')

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

const filteredOrders = computed(() => {
  if (!statusFilter.value) return orders.value
  return orders.value.filter(o => o.status === statusFilter.value)
})

const fetchOrders = async () => {
  try {
    orders.value = await orderService.getOrders()
  } catch (error) {
    console.error('Failed to fetch orders', error)
  }
}

const handleStatusChange = async (id: number, status: string) => {
  try {
    await orderService.updateOrderStatus(id, status)
    await fetchOrders()
  } catch (error) {
    console.error('Failed to update order status', error)
    alert('状态更新失败')
  }
}

onMounted(fetchOrders)
</script>

<style scoped>
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.filter-group select {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.count {
  color: #888;
  font-size: 0.9rem;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
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
  font-size: 0.9rem;
}

.data-table a {
  color: #e94560;
}

.amount {
  font-weight: bold;
}

.status-badge {
  display: inline-block;
  padding: 0.2rem 0.5rem;
  border-radius: 12px;
  font-size: 0.8rem;
  color: #fff;
}

.status-badge.pending { background-color: #f0ad4e; }
.status-badge.paid { background-color: #5bc0de; }
.status-badge.shipped { background-color: #0275d8; }
.status-badge.delivered { background-color: #5cb85c; }
.status-badge.cancelled { background-color: #d9534f; }

.btn-sm {
  padding: 0.25rem 0.5rem;
  font-size: 0.8rem;
  margin-right: 0.25rem;
  background: #eee;
}

.status-select {
  padding: 0.2rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.8rem;
}
</style>
