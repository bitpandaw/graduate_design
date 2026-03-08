import axios from 'axios'
import type { Product, User, Order, CartItem } from '@/types'

const apiClient = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// JWT 请求拦截器
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器：处理 401
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token')
      localStorage.removeItem('auth_user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// ── 认证服务 ──
export const authService = {
  async login(credentials: { username: string; password: string }) {
    const response = await apiClient.post('/auth/login', credentials)
    return response.data
  },

  async register(data: { username: string; email: string; password: string }) {
    const response = await apiClient.post('/auth/register', data)
    return response.data
  },
}

// ── 用户服务 ──
export const userService = {
  async getUsers() {
    const response = await apiClient.get('/users')
    return response.data
  },

  async getUserById(id: number) {
    const response = await apiClient.get(`/users/${id}`)
    return response.data
  },

  async updateUser(id: number, data: Partial<User>) {
    const response = await apiClient.put(`/users/${id}`, data)
    return response.data
  },

  async deleteUser(id: number) {
    const response = await apiClient.delete(`/users/${id}`)
    return response.data
  },
}

// ── 商品服务 ──
export const productService = {
  async getProducts() {
    const response = await apiClient.get('/products')
    return response.data
  },

  async getProductById(id: number) {
    const response = await apiClient.get(`/products/${id}`)
    return response.data
  },

  async getProductsByCategory(category: string) {
    const response = await apiClient.get(`/products/category/${category}`)
    return response.data
  },

  async searchProducts(keyword: string) {
    const response = await apiClient.get('/products/search', { params: { keyword } })
    return response.data
  },

  async createProduct(data: Omit<Product, 'id'>) {
    const response = await apiClient.post('/products', data)
    return response.data
  },

  async updateProduct(id: number, data: Partial<Product>) {
    const response = await apiClient.put(`/products/${id}`, data)
    return response.data
  },

  async deleteProduct(id: number) {
    const response = await apiClient.delete(`/products/${id}`)
    return response.data
  },
}

// ── 订单服务 ──
export const orderService = {
  async getOrders() {
    const response = await apiClient.get('/orders')
    return response.data
  },

  async getOrderById(id: number) {
    const response = await apiClient.get(`/orders/${id}`)
    return response.data
  },

  async getOrdersByUserId(userId: number) {
    const response = await apiClient.get(`/orders/user/${userId}`)
    return response.data
  },

  async createOrder(order: unknown) {
    const response = await apiClient.post('/orders', order)
    return response.data
  },

  async updateOrderStatus(id: number, status: string) {
    const response = await apiClient.put(`/orders/${id}/status`, { status })
    return response.data
  },

  async cancelOrder(id: number) {
    const response = await apiClient.put(`/orders/${id}/status`, { status: 'CANCELLED' })
    return response.data
  },
}

// ── 推荐服务 ──
export const recommendationService = {
  async getRecommendations(userId: number, limit: number = 10) {
    const response = await apiClient.get(`/recommendations/user/${userId}`, {
      params: { limit },
    })
    return response.data
  },
}

// ── 支付服务 ──
export const paymentService = {
  async createPayment(payment: unknown) {
    const response = await apiClient.post('/payments', payment)
    return response.data
  },

  async getPaymentByOrderId(orderId: number) {
    const response = await apiClient.get(`/payments/order/${orderId}`)
    return response.data
  },
}

// ── 搜索服务 ──
export const searchService = {
  async search(query: string, filters?: { category?: string; minPrice?: number; maxPrice?: number }) {
    const response = await apiClient.get('/search', { params: { q: query, ...filters } })
    return response.data
  },
}

// ── 购物车服务（客户端本地存储） ──
const CART_KEY = 'mall_cart'

export const cartService = {
  getCart(): CartItem[] {
    const data = localStorage.getItem(CART_KEY)
    return data ? JSON.parse(data) : []
  },

  addToCart(item: CartItem) {
    const cart = this.getCart()
    const existing = cart.find(c => c.productId === item.productId)
    if (existing) {
      existing.quantity += item.quantity
    } else {
      cart.push(item)
    }
    localStorage.setItem(CART_KEY, JSON.stringify(cart))
    return cart
  },

  updateQuantity(productId: number, quantity: number) {
    const cart = this.getCart()
    const item = cart.find(c => c.productId === productId)
    if (item) {
      item.quantity = quantity
      if (item.quantity <= 0) {
        return this.removeFromCart(productId)
      }
    }
    localStorage.setItem(CART_KEY, JSON.stringify(cart))
    return cart
  },

  removeFromCart(productId: number) {
    const cart = this.getCart().filter(c => c.productId !== productId)
    localStorage.setItem(CART_KEY, JSON.stringify(cart))
    return cart
  },

  clearCart() {
    localStorage.removeItem(CART_KEY)
    return []
  },

  getTotal(): number {
    return this.getCart().reduce((sum, item) => sum + item.price * item.quantity, 0)
  },
}

// ── 管理端统计服务 ──
export const adminService = {
  async getDashboardStats() {
    const [users, products, orders] = await Promise.all([
      apiClient.get('/users'),
      apiClient.get('/products'),
      apiClient.get('/orders'),
    ])
    const orderList = orders.data as Order[]
    const totalRevenue = orderList
      .filter((o: Order) => o.status !== 'CANCELLED')
      .reduce((sum: number, o: Order) => sum + o.totalAmount, 0)
    return {
      totalUsers: (users.data as User[]).length,
      totalProducts: (products.data as Product[]).length,
      totalOrders: orderList.length,
      totalRevenue,
      recentOrders: orderList.slice(0, 10),
    }
  },
}
