<template>
  <div>
    <div class="stats-grid">
      <div class="stat-card card">
        <div class="stat-value">{{ stats.totalUsers }}</div>
        <div class="stat-label">注册用户</div>
      </div>
      <div class="stat-card card">
        <div class="stat-value">{{ stats.totalProducts }}</div>
        <div class="stat-label">商品总数</div>
      </div>
      <div class="stat-card card">
        <div class="stat-value">{{ stats.totalOrders }}</div>
        <div class="stat-label">订单总数</div>
      </div>
      <div class="stat-card card">
        <div class="stat-value">¥{{ stats.totalRevenue.toFixed(2) }}</div>
        <div class="stat-label">总营收</div>
      </div>
    </div>

    <div class="card">
      <h3>最近订单</h3>
      <table class="data-table">
        <thead>
          <tr>
            <th>订单ID</th>
            <th>用户ID</th>
            <th>金额</th>
            <th>状态</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="order in stats.recentOrders" :key="order.id">
            <td>
              <router-link :to="`/admin/orders/${order.id}`">#{{ order.id }}</router-link>
            </td>
            <td>{{ order.userId }}</td>
            <td class="amount">¥{{ order.totalAmount }}</td>
            <td>
              <span class="status-badge" :class="order.status.toLowerCase()">
                {{ statusText(order.status) }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, onMounted } from 'vue'
import { adminService } from '@/services/apiService'
import type { Order } from '@/types'

const stats = reactive({
  totalUsers: 0,
  totalProducts: 0,
  totalOrders: 0,
  totalRevenue: 0,
  recentOrders: [] as Order[],
})

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
    const data = await adminService.getDashboardStats()
    Object.assign(stats, data)
  } catch (error) {
    console.error('Failed to fetch dashboard stats', error)
  }
})
</script>

<style scoped>
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.stat-card {
  text-align: center;
  padding: 1.5rem;
}

.stat-value {
  font-size: 1.75rem;
  font-weight: bold;
  color: #e94560;
  margin-bottom: 0.5rem;
}

.stat-label {
  color: #888;
  font-size: 0.9rem;
}

h3 {
  margin-bottom: 1rem;
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

.data-table td a {
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
</style>
