<template>
  <div class="admin-layout">
    <aside class="admin-sidebar">
      <div class="sidebar-brand">
        <router-link to="/admin">管理后台</router-link>
      </div>
      <nav class="sidebar-nav">
        <router-link to="/admin" :class="{ active: route.path === '/admin' }">
          <span class="nav-icon">📊</span> 仪表盘
        </router-link>
        <router-link to="/admin/users" active-class="active">
          <span class="nav-icon">👥</span> 用户管理
        </router-link>
        <router-link to="/admin/products" active-class="active">
          <span class="nav-icon">📦</span> 商品管理
        </router-link>
        <router-link to="/admin/orders" active-class="active">
          <span class="nav-icon">📋</span> 订单管理
        </router-link>
        <router-link to="/admin/analytics" active-class="active">
          <span class="nav-icon">📈</span> 数据分析
        </router-link>
      </nav>
      <div class="sidebar-footer">
        <router-link to="/">← 返回前台</router-link>
      </div>
    </aside>
    <div class="admin-main">
      <header class="admin-header">
        <h2>{{ pageTitle }}</h2>
        <span class="admin-user">管理员: {{ username }}</span>
      </header>
      <div class="admin-content">
        <router-view />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuth } from '@/composables/useAuth'

const route = useRoute()
const { username } = useAuth()

const pageTitleMap: Record<string, string> = {
  '/admin': '仪表盘',
  '/admin/users': '用户管理',
  '/admin/products': '商品管理',
  '/admin/orders': '订单管理',
  '/admin/analytics': '数据分析',
}

const pageTitle = computed(() => {
  for (const [path, title] of Object.entries(pageTitleMap)) {
    if (route.path === path || route.path.startsWith(path + '/')) {
      return title
    }
  }
  return '管理后台'
})
</script>

<style scoped>
.admin-layout {
  display: flex;
  min-height: 100vh;
}

.admin-sidebar {
  width: 220px;
  background-color: #1a1a2e;
  color: #fff;
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  z-index: 100;
}

.sidebar-brand {
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid #2a2a4e;
}

.sidebar-brand a {
  color: #e94560;
  text-decoration: none;
  font-size: 1.2rem;
  font-weight: bold;
}

.sidebar-nav {
  flex: 1;
  padding: 1rem 0;
}

.sidebar-nav a {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1.5rem;
  color: #ccc;
  text-decoration: none;
  border-left: 3px solid transparent;
  transition: all 0.2s;
}

.sidebar-nav a:hover {
  background: #16213e;
  color: #fff;
}

.sidebar-nav a.active {
  background: #16213e;
  color: #e94560;
  border-left-color: #e94560;
}

.nav-icon {
  font-size: 1.1rem;
}

.sidebar-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid #2a2a4e;
}

.sidebar-footer a {
  color: #aaa;
  text-decoration: none;
  font-size: 0.9rem;
}

.sidebar-footer a:hover {
  color: #e94560;
}

.admin-main {
  flex: 1;
  margin-left: 220px;
  background: #f5f5f5;
  min-height: 100vh;
}

.admin-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2rem;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.admin-header h2 {
  font-size: 1.25rem;
  color: #333;
}

.admin-user {
  color: #888;
  font-size: 0.9rem;
}

.admin-content {
  padding: 1.5rem 2rem;
}
</style>
