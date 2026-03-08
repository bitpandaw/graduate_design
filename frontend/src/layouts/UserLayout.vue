<template>
  <div class="user-layout">
    <nav class="navbar">
      <div class="nav-brand">
        <router-link to="/">电商推荐系统</router-link>
      </div>
      <div class="nav-links">
        <router-link to="/">首页</router-link>
        <router-link to="/products">商品</router-link>
        <router-link to="/search">搜索</router-link>
        <router-link to="/my-orders">我的订单</router-link>
        <router-link to="/cart">购物车</router-link>
      </div>
      <div class="nav-actions">
        <template v-if="isLoggedIn">
          <router-link to="/profile">{{ username }}</router-link>
          <router-link to="/admin" v-if="isAdmin" class="admin-link">管理后台</router-link>
          <a href="#" @click.prevent="handleLogout">退出</a>
        </template>
        <router-link v-else to="/login">登录</router-link>
      </div>
    </nav>
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { useAuth } from '@/composables/useAuth'
import { useRouter } from 'vue-router'

const { isLoggedIn, isAdmin, username, clearAuth } = useAuth()
const router = useRouter()

const handleLogout = () => {
  clearAuth()
  router.push('/')
}
</script>

<style scoped>
.navbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 2rem;
  height: 60px;
  background-color: #1a1a2e;
  color: #fff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.nav-brand a {
  font-size: 1.25rem;
  font-weight: bold;
  color: #e94560;
  text-decoration: none;
}

.nav-links {
  display: flex;
  gap: 1.5rem;
}

.nav-links a {
  color: #eee;
  text-decoration: none;
  padding: 0.5rem 0;
  border-bottom: 2px solid transparent;
  transition: border-color 0.2s;
}

.nav-links a:hover,
.nav-links a.router-link-active {
  border-bottom-color: #e94560;
  color: #fff;
}

.nav-actions {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.nav-actions a {
  color: #eee;
  text-decoration: none;
  font-size: 0.9rem;
  transition: color 0.2s;
}

.nav-actions a:hover {
  color: #e94560;
}

.admin-link {
  background: #e94560;
  color: #fff !important;
  padding: 0.3rem 0.75rem;
  border-radius: 4px;
  font-size: 0.85rem;
}

.admin-link:hover {
  background: #c73e54;
}

.main-content {
  max-width: 1200px;
  margin: 2rem auto;
  padding: 0 1rem;
}
</style>
