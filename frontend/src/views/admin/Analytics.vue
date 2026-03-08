<template>
  <div>
    <div class="stats-grid">
      <div class="stat-card card">
        <h3>订单状态分布</h3>
        <div class="stat-bars">
          <div class="bar-item" v-for="item in orderStatusDist" :key="item.status">
            <span class="bar-label">{{ item.label }}</span>
            <div class="bar-track">
              <div
                class="bar-fill"
                :style="{ width: item.percentage + '%' }"
                :class="item.status.toLowerCase()"
              ></div>
            </div>
            <span class="bar-value">{{ item.count }}</span>
          </div>
        </div>
      </div>

      <div class="stat-card card">
        <h3>商品分类分布</h3>
        <div class="stat-bars">
          <div class="bar-item" v-for="item in categoryDist" :key="item.category">
            <span class="bar-label">{{ item.label }}</span>
            <div class="bar-track">
              <div class="bar-fill category-bar" :style="{ width: item.percentage + '%' }"></div>
            </div>
            <span class="bar-value">{{ item.count }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="card top-products-card">
      <div class="top-products-header">
        <h3>销售额 Top 10 商品</h3>
        <span class="total-sales" v-if="topProducts.length">
          Top 10 总销售额：<strong>¥{{ topProductsTotalSales }}</strong>
        </span>
      </div>
      <div class="top-products-empty" v-if="!topProducts.length">暂无销售数据</div>
      <div class="top-products-list" v-else>
        <div
          class="top-product-row"
          v-for="(product, index) in topProducts"
          :key="product.id"
          :class="{ 'top-rank': index < 3 }"
        >
          <div class="rank-badge" :class="'rank-' + (index + 1)">
            {{ index + 1 }}
          </div>
          <div class="product-info">
            <div class="product-name">{{ product.name }}</div>
            <div class="product-meta">
              <span class="meta-tag">{{ categoryLabels[product.category] || product.category }}</span>
              <span class="meta-price">单价 ¥{{ product.price }}</span>
              <span class="meta-qty">售出 {{ product.soldCount }} 件</span>
            </div>
          </div>
          <div class="sales-section">
            <div class="sales-amount">¥{{ product.sales?.toFixed(2) }}</div>
            <div class="sales-bar-track">
              <div
                class="sales-bar-fill"
                :style="{ width: product.salesPercent + '%' }"
                :class="'rank-bar-' + Math.min(index + 1, 4)"
              ></div>
            </div>
            <div class="sales-percent">{{ product.salesPercent?.toFixed(1) }}%</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { productService, orderService } from '@/services/apiService'
import type { Product, Order } from '@/types'

interface StatusDist {
  status: string
  label: string
  count: number
  percentage: number
}

interface CategoryDist {
  category: string
  label: string
  count: number
  percentage: number
}

const orderStatusDist = ref<StatusDist[]>([])
const categoryDist = ref<CategoryDist[]>([])
const topProducts = ref<(Product & { sales?: number; soldCount?: number; salesPercent?: number })[]>([])
const topProductsTotalSales = ref('0.00')

const statusLabels: Record<string, string> = {
  PENDING: '待付款',
  PAID: '已付款',
  SHIPPED: '已发货',
  DELIVERED: '已送达',
  CANCELLED: '已取消',
}

const categoryLabels: Record<string, string> = {
  ELECTRONICS: '电子产品',
  CLOTHING: '服装',
  HOME_GOODS: '家居',
  BOOKS: '图书',
  SPORTS: '运动',
}

onMounted(async () => {
  try {
    const [orders, products] = await Promise.all([
      orderService.getOrders(),
      productService.getProducts(),
    ]) as [Order[], Product[]]

    // 订单状态分布
    const statusCounts: Record<string, number> = {}
    orders.forEach(o => {
      statusCounts[o.status] = (statusCounts[o.status] || 0) + 1
    })
    const maxStatusCount = Math.max(...Object.values(statusCounts), 1)
    orderStatusDist.value = Object.entries(statusCounts).map(([status, count]) => ({
      status,
      label: statusLabels[status] || status,
      count,
      percentage: (count / maxStatusCount) * 100,
    }))

    // 商品分类分布
    const catCounts: Record<string, number> = {}
    products.forEach(p => {
      catCounts[p.category] = (catCounts[p.category] || 0) + 1
    })
    const maxCatCount = Math.max(...Object.values(catCounts), 1)
    categoryDist.value = Object.entries(catCounts).map(([category, count]) => ({
      category,
      label: categoryLabels[category] || category,
      count,
      percentage: (count / maxCatCount) * 100,
    }))

    // Top 10 按实际销售额排序（从订单明细中聚合）
    const salesMap = new Map<number, number>()
    const soldCountMap = new Map<number, number>()
    orders
      .filter(o => o.status !== 'CANCELLED')
      .forEach(o => {
        if (o.items) {
          o.items.forEach(item => {
            salesMap.set(item.productId, (salesMap.get(item.productId) || 0) + item.price * item.quantity)
            soldCountMap.set(item.productId, (soldCountMap.get(item.productId) || 0) + item.quantity)
          })
        }
      })
    const productMap = new Map(products.map(p => [p.id, p]))
    const sorted = [...salesMap.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .filter(([id]) => productMap.has(id))
    const maxSales = sorted.length ? sorted[0][1] : 1
    const totalSales = sorted.reduce((sum, [, s]) => sum + s, 0)
    topProductsTotalSales.value = totalSales.toFixed(2)
    topProducts.value = sorted.map(([id, sales]) => ({
      ...productMap.get(id)!,
      sales,
      soldCount: soldCountMap.get(id) || 0,
      salesPercent: (sales / maxSales) * 100,
    }))
  } catch (error) {
    console.error('Failed to fetch analytics data', error)
  }
})
</script>

<style scoped>
.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.stat-card h3 {
  margin-bottom: 1rem;
}

.bar-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.bar-label {
  width: 60px;
  font-size: 0.85rem;
  color: #555;
}

.bar-track {
  flex: 1;
  height: 20px;
  background: #f0f0f0;
  border-radius: 4px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.5s ease;
}

.bar-fill.pending { background: #f0ad4e; }
.bar-fill.paid { background: #5bc0de; }
.bar-fill.shipped { background: #0275d8; }
.bar-fill.delivered { background: #5cb85c; }
.bar-fill.cancelled { background: #d9534f; }
.bar-fill.category-bar { background: #e94560; }

.bar-value {
  width: 40px;
  text-align: right;
  font-weight: bold;
  font-size: 0.9rem;
}

h3 { margin-bottom: 1rem; }

/* Top Products */
.top-products-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.top-products-header h3 {
  margin-bottom: 0;
}

.total-sales {
  font-size: 0.9rem;
  color: #888;
}

.total-sales strong {
  color: #e94560;
  font-size: 1rem;
}

.top-products-empty {
  text-align: center;
  color: #aaa;
  padding: 2rem 0;
}

.top-products-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.top-product-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  background: #fafafa;
  transition: background 0.2s;
}

.top-product-row:hover {
  background: #f0f0f5;
}

.top-product-row.top-rank {
  background: #fff8f0;
}

.top-product-row.top-rank:hover {
  background: #fff0e0;
}

.rank-badge {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 0.85rem;
  flex-shrink: 0;
  background: #e8e8e8;
  color: #666;
}

.rank-badge.rank-1 {
  background: linear-gradient(135deg, #f6d365, #f5a623);
  color: #fff;
  box-shadow: 0 2px 6px rgba(245, 166, 35, 0.4);
}

.rank-badge.rank-2 {
  background: linear-gradient(135deg, #c0c0c0, #a8a8a8);
  color: #fff;
  box-shadow: 0 2px 6px rgba(168, 168, 168, 0.4);
}

.rank-badge.rank-3 {
  background: linear-gradient(135deg, #d4a373, #bc8456);
  color: #fff;
  box-shadow: 0 2px 6px rgba(188, 132, 86, 0.4);
}

.product-info {
  flex: 1;
  min-width: 0;
}

.product-name {
  font-weight: 600;
  font-size: 0.95rem;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.product-meta {
  display: flex;
  gap: 0.75rem;
  margin-top: 0.25rem;
  font-size: 0.8rem;
  color: #999;
}

.meta-tag {
  background: #f0f0f0;
  padding: 0 6px;
  border-radius: 3px;
  color: #666;
}

.sales-section {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-shrink: 0;
  width: 320px;
}

.sales-amount {
  width: 100px;
  text-align: right;
  font-weight: bold;
  color: #e94560;
  font-size: 0.95rem;
}

.sales-bar-track {
  flex: 1;
  height: 8px;
  background: #f0f0f0;
  border-radius: 4px;
  overflow: hidden;
}

.sales-bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.6s ease;
}

.sales-bar-fill.rank-bar-1 { background: linear-gradient(90deg, #f5a623, #f6d365); }
.sales-bar-fill.rank-bar-2 { background: linear-gradient(90deg, #a8a8a8, #c0c0c0); }
.sales-bar-fill.rank-bar-3 { background: linear-gradient(90deg, #bc8456, #d4a373); }
.sales-bar-fill.rank-bar-4 { background: #e94560; }

.sales-percent {
  width: 50px;
  text-align: right;
  font-size: 0.8rem;
  color: #999;
}
</style>
