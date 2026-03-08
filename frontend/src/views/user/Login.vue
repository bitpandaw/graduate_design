<template>
  <div class="login-page">
    <div class="login-card card">
      <h1>{{ isRegister ? '注册' : '登录' }}</h1>

      <form @submit.prevent="handleSubmit">
        <div class="form-group">
          <label>用户名</label>
          <input v-model="form.username" type="text" required placeholder="请输入用户名" />
        </div>

        <div class="form-group" v-if="isRegister">
          <label>邮箱</label>
          <input v-model="form.email" type="email" required placeholder="请输入邮箱" />
        </div>

        <div class="form-group">
          <label>密码</label>
          <input v-model="form.password" type="password" required placeholder="请输入密码" />
        </div>

        <p class="error" v-if="error">{{ error }}</p>

        <button class="btn btn-primary btn-full" type="submit" :disabled="loading">
          {{ loading ? '处理中...' : (isRegister ? '注册' : '登录') }}
        </button>
      </form>

      <p class="toggle">
        {{ isRegister ? '已有账号？' : '没有账号？' }}
        <a href="#" @click.prevent="isRegister = !isRegister">
          {{ isRegister ? '去登录' : '去注册' }}
        </a>
      </p>

      <div class="demo-login">
        <p>快速体验（演示账号）：</p>
        <div class="demo-buttons">
          <button class="btn" @click="demoLogin('USER')">普通用户</button>
          <button class="btn" @click="demoLogin('ADMIN')">管理员</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuth } from '@/composables/useAuth'

const router = useRouter()
const route = useRoute()
const { setAuth } = useAuth()

const isRegister = ref(false)
const loading = ref(false)
const error = ref('')

const form = reactive({
  username: '',
  email: '',
  password: '',
})

const handleSubmit = async () => {
  error.value = ''
  loading.value = true

  try {
    // 简化登录：直接模拟认证（后端暂无 auth 端点）
    const mockUser = {
      id: 1,
      username: form.username,
      role: 'USER' as const,
    }
    setAuth(mockUser, 'mock-token-' + Date.now())

    const redirect = (route.query.redirect as string) || '/'
    router.push(redirect)
  } catch {
    error.value = isRegister.value ? '注册失败，请重试' : '登录失败，请检查用户名和密码'
  } finally {
    loading.value = false
  }
}

const demoLogin = (role: 'USER' | 'ADMIN') => {
  const user = {
    id: role === 'ADMIN' ? 1 : 2,
    username: role === 'ADMIN' ? 'admin' : 'user',
    role,
  }
  setAuth(user, 'demo-token-' + role.toLowerCase())

  const redirect = (route.query.redirect as string) || (role === 'ADMIN' ? '/admin' : '/')
  router.push(redirect)
}
</script>

<style scoped>
.login-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 60vh;
}

.login-card {
  width: 100%;
  max-width: 400px;
  padding: 2rem;
}

h1 {
  text-align: center;
  margin-bottom: 2rem;
}

.form-group {
  margin-bottom: 1.25rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #555;
}

.form-group input {
  width: 100%;
  padding: 0.6rem 1rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

.form-group input:focus {
  outline: none;
  border-color: #e94560;
}

.error {
  color: #d9534f;
  font-size: 0.9rem;
  margin-bottom: 1rem;
}

.btn-full {
  width: 100%;
  padding: 0.75rem;
  font-size: 1rem;
}

.toggle {
  text-align: center;
  margin-top: 1.25rem;
  color: #888;
}

.toggle a {
  color: #e94560;
}

.demo-login {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid #eee;
  text-align: center;
}

.demo-login p {
  color: #888;
  font-size: 0.9rem;
  margin-bottom: 0.75rem;
}

.demo-buttons {
  display: flex;
  gap: 0.75rem;
  justify-content: center;
}

.demo-buttons .btn {
  background: #16213e;
  color: #fff;
}

.demo-buttons .btn:hover {
  background: #1a1a2e;
}
</style>
