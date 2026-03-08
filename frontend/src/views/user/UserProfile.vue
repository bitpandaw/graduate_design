<template>
  <div>
    <h1>个人中心</h1>

    <div class="card" v-if="user">
      <div class="profile-header">
        <div class="avatar">{{ user.username?.charAt(0)?.toUpperCase() }}</div>
        <div>
          <h2>{{ user.username }}</h2>
          <span class="level" :class="user.level?.toLowerCase()">{{ user.level }}</span>
        </div>
      </div>

      <div class="info-grid">
        <div class="info-item">
          <label>邮箱</label>
          <p>{{ user.email }}</p>
        </div>
        <div class="info-item">
          <label>账户余额</label>
          <p class="balance">¥{{ user.balance }}</p>
        </div>
      </div>
    </div>

    <div class="card quick-links">
      <h3>快捷入口</h3>
      <div class="links">
        <router-link to="/my-orders" class="link-card">
          <span class="link-icon">📋</span>
          <span>我的订单</span>
        </router-link>
        <router-link to="/cart" class="link-card">
          <span class="link-icon">🛒</span>
          <span>购物车</span>
        </router-link>
        <router-link to="/products" class="link-card">
          <span class="link-icon">📦</span>
          <span>浏览商品</span>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { userService } from '@/services/apiService'
import { useAuth } from '@/composables/useAuth'
import type { User } from '@/types'

const { userId } = useAuth()
const user = ref<User | null>(null)

onMounted(async () => {
  if (!userId.value) return
  try {
    user.value = await userService.getUserById(userId.value)
  } catch (error) {
    console.error('Failed to fetch user profile', error)
  }
})
</script>

<style scoped>
h1 { margin-bottom: 1.5rem; }

.profile-header {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.avatar {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: linear-gradient(135deg, #e94560, #c73e54);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  font-weight: bold;
}

.level {
  display: inline-block;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-size: 0.85rem;
  color: #fff;
  margin-top: 0.25rem;
}

.level.bronze { background-color: #cd7f32; }
.level.silver { background-color: #c0c0c0; color: #333; }
.level.gold { background-color: #ffd700; color: #333; }
.level.platinum { background-color: #e5e4e2; color: #333; }

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.info-item label {
  display: block;
  color: #888;
  font-size: 0.85rem;
  margin-bottom: 0.25rem;
}

.balance {
  color: #e94560;
  font-weight: bold;
  font-size: 1.2rem;
}

.quick-links {
  margin-top: 1rem;
}

.quick-links h3 {
  margin-bottom: 1rem;
}

.links {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
}

.link-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding: 1.5rem;
  background: #f9f9f9;
  border-radius: 8px;
  text-decoration: none;
  color: #333;
  transition: background 0.2s;
}

.link-card:hover {
  background: #f0f0f0;
}

.link-icon {
  font-size: 1.5rem;
}
</style>
