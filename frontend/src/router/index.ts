import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuth } from '@/composables/useAuth'
import UserLayout from '@/layouts/UserLayout.vue'
import AdminLayout from '@/layouts/AdminLayout.vue'

const routes: RouteRecordRaw[] = [
  // 用户前台路由
  {
    path: '/',
    component: UserLayout,
    children: [
      {
        path: '',
        name: 'Home',
        component: () => import('@/views/user/Home.vue'),
      },
      {
        path: 'products',
        name: 'ProductBrowse',
        component: () => import('@/views/user/ProductBrowse.vue'),
      },
      {
        path: 'products/:id',
        name: 'ProductDetail',
        component: () => import('@/views/user/ProductDetail.vue'),
        props: true,
      },
      {
        path: 'search',
        name: 'SearchResults',
        component: () => import('@/views/user/SearchResults.vue'),
      },
      {
        path: 'cart',
        name: 'Cart',
        component: () => import('@/views/user/Cart.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'checkout',
        name: 'Checkout',
        component: () => import('@/views/user/Checkout.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'my-orders',
        name: 'MyOrders',
        component: () => import('@/views/user/MyOrders.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'my-orders/:id',
        name: 'OrderDetail',
        component: () => import('@/views/user/OrderDetail.vue'),
        meta: { requiresAuth: true },
        props: true,
      },
      {
        path: 'profile',
        name: 'UserProfile',
        component: () => import('@/views/user/UserProfile.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'login',
        name: 'Login',
        component: () => import('@/views/user/Login.vue'),
      },
    ],
  },

  // 管理后台路由
  {
    path: '/admin',
    component: AdminLayout,
    meta: { requiresAuth: true, requiresAdmin: true },
    children: [
      {
        path: '',
        name: 'AdminDashboard',
        component: () => import('@/views/admin/Dashboard.vue'),
      },
      {
        path: 'users',
        name: 'AdminUserManage',
        component: () => import('@/views/admin/UserManage.vue'),
      },
      {
        path: 'users/:id',
        name: 'AdminUserDetail',
        component: () => import('@/views/admin/UserDetail.vue'),
        props: true,
      },
      {
        path: 'products',
        name: 'AdminProductManage',
        component: () => import('@/views/admin/ProductManage.vue'),
      },
      {
        path: 'products/new',
        name: 'AdminProductCreate',
        component: () => import('@/views/admin/ProductEdit.vue'),
      },
      {
        path: 'products/:id/edit',
        name: 'AdminProductEdit',
        component: () => import('@/views/admin/ProductEdit.vue'),
        props: true,
      },
      {
        path: 'orders',
        name: 'AdminOrderManage',
        component: () => import('@/views/admin/OrderManage.vue'),
      },
      {
        path: 'orders/:id',
        name: 'AdminOrderDetail',
        component: () => import('@/views/admin/OrderDetail.vue'),
        props: true,
      },
      {
        path: 'analytics',
        name: 'AdminAnalytics',
        component: () => import('@/views/admin/Analytics.vue'),
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 导航守卫
router.beforeEach((to, _from, next) => {
  const { isLoggedIn, isAdmin } = useAuth()

  if (to.matched.some(record => record.meta.requiresAuth) && !isLoggedIn.value) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
    return
  }

  if (to.matched.some(record => record.meta.requiresAdmin) && !isAdmin.value) {
    next({ name: 'Home' })
    return
  }

  next()
})

export default router
