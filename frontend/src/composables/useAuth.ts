import { ref, computed } from 'vue'

interface AuthUser {
  id: number
  username: string
  role: 'USER' | 'ADMIN'
}

const currentUser = ref<AuthUser | null>(null)
const token = ref<string | null>(localStorage.getItem('auth_token'))

// 初始化时尝试从 localStorage 恢复用户信息
const savedUser = localStorage.getItem('auth_user')
if (savedUser) {
  try {
    currentUser.value = JSON.parse(savedUser)
  } catch {
    localStorage.removeItem('auth_user')
  }
}

export function useAuth() {
  const isLoggedIn = computed(() => !!token.value && !!currentUser.value)
  const isAdmin = computed(() => currentUser.value?.role === 'ADMIN')
  const username = computed(() => currentUser.value?.username ?? '')
  const userId = computed(() => currentUser.value?.id ?? 0)

  function setAuth(user: AuthUser, authToken: string) {
    currentUser.value = user
    token.value = authToken
    localStorage.setItem('auth_token', authToken)
    localStorage.setItem('auth_user', JSON.stringify(user))
  }

  function clearAuth() {
    currentUser.value = null
    token.value = null
    localStorage.removeItem('auth_token')
    localStorage.removeItem('auth_user')
  }

  return { currentUser, isLoggedIn, isAdmin, username, userId, setAuth, clearAuth }
}
