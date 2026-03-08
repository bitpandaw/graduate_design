<template>
  <div v-if="user">
    <div class="breadcrumb">
      <router-link to="/admin/users">用户管理</router-link> / {{ user.username }}
    </div>

    <div class="card">
      <h2>用户信息</h2>
      <form @submit.prevent="handleSave">
        <div class="form-grid">
          <div class="form-group">
            <label>用户名</label>
            <input v-model="user.username" />
          </div>
          <div class="form-group">
            <label>邮箱</label>
            <input v-model="user.email" type="email" />
          </div>
          <div class="form-group">
            <label>等级</label>
            <select v-model="user.level">
              <option value="BRONZE">铜牌</option>
              <option value="SILVER">银牌</option>
              <option value="GOLD">金牌</option>
              <option value="PLATINUM">白金</option>
            </select>
          </div>
          <div class="form-group">
            <label>余额</label>
            <input v-model.number="user.balance" type="number" step="0.01" />
          </div>
        </div>
        <div class="actions">
          <button class="btn btn-primary" type="submit">保存修改</button>
          <router-link to="/admin/users" class="btn">返回列表</router-link>
        </div>
      </form>
    </div>

    <div class="card">
      <h2>用户订单</h2>
      <table class="data-table" v-if="orders.length">
        <thead>
          <tr>
            <th>订单ID</th>
            <th>金额</th>
            <th>状态</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="order in orders" :key="order.id">
            <td>
              <router-link :to="`/admin/orders/${order.id}`">#{{ order.id }}</router-link>
            </td>
            <td>¥{{ order.totalAmount }}</td>
            <td>{{ order.status }}</td>
          </tr>
        </tbody>
      </table>
      <p v-else class="empty">暂无订单记录</p>
    </div>
  </div>
  <div v-else class="loading">加载中...</div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { userService, orderService } from '@/services/apiService'
import type { User, Order } from '@/types'

const props = defineProps<{ id: string }>()

const user = ref<User | null>(null)
const orders = ref<Order[]>([])

onMounted(async () => {
  try {
    user.value = await userService.getUserById(Number(props.id))
    try {
      orders.value = await orderService.getOrdersByUserId(Number(props.id))
    } catch {
      // 可能没有订单
    }
  } catch (error) {
    console.error('Failed to fetch user', error)
  }
})

const handleSave = async () => {
  if (!user.value) return
  try {
    await userService.updateUser(user.value.id, user.value)
    alert('保存成功')
  } catch (error) {
    console.error('Failed to update user', error)
    alert('保存失败')
  }
}
</script>

<style scoped>
.breadcrumb {
  margin-bottom: 1rem;
  color: #888;
}

.breadcrumb a { color: #e94560; }

h2 { margin-bottom: 1rem; }

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  color: #555;
  font-weight: 500;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.actions {
  display: flex;
  gap: 0.75rem;
}

.actions .btn:last-child {
  background: #eee;
  color: #666;
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
}

.data-table td a { color: #e94560; }

.empty, .loading {
  text-align: center;
  color: #999;
  padding: 2rem 0;
}
</style>
