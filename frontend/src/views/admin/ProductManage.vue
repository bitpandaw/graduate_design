<template>
  <div>
    <div class="toolbar">
      <input v-model="searchTerm" placeholder="搜索商品..." class="search-input" />
      <div class="toolbar-right">
        <select v-model="categoryFilter" @change="filterProducts">
          <option value="">全部分类</option>
          <option value="ELECTRONICS">电子产品</option>
          <option value="CLOTHING">服装</option>
          <option value="HOME_GOODS">家居</option>
          <option value="BOOKS">图书</option>
          <option value="SPORTS">运动</option>
        </select>
        <router-link to="/admin/products/new" class="btn btn-primary">新增商品</router-link>
      </div>
    </div>

    <div class="card">
      <table class="data-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>名称</th>
            <th>价格</th>
            <th>库存</th>
            <th>分类</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="product in filteredProducts" :key="product.id">
            <td>{{ product.id }}</td>
            <td>{{ product.name }}</td>
            <td class="price">¥{{ product.price }}</td>
            <td>
              <span :class="{ 'low-stock': product.stock < 100 }">{{ product.stock }}</span>
            </td>
            <td>{{ product.category }}</td>
            <td>
              <router-link :to="`/admin/products/${product.id}/edit`" class="btn btn-sm">编辑</router-link>
              <button class="btn btn-sm btn-danger" @click="handleDelete(product.id)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { productService } from '@/services/apiService'
import type { Product } from '@/types'

const products = ref<Product[]>([])
const searchTerm = ref('')
const categoryFilter = ref('')

const filteredProducts = computed(() => {
  let list = products.value
  if (categoryFilter.value) {
    list = list.filter(p => p.category === categoryFilter.value)
  }
  if (searchTerm.value.trim()) {
    const term = searchTerm.value.toLowerCase()
    list = list.filter(p => p.name.toLowerCase().includes(term))
  }
  return list
})

const filterProducts = () => { /* computed handles it */ }

const fetchProducts = async () => {
  try {
    products.value = await productService.getProducts()
  } catch (error) {
    console.error('Failed to fetch products', error)
  }
}

const handleDelete = async (id: number) => {
  if (!confirm('确定要删除此商品吗？')) return
  try {
    await productService.deleteProduct(id)
    await fetchProducts()
  } catch (error) {
    console.error('Failed to delete product', error)
    alert('删除失败')
  }
}

onMounted(fetchProducts)
</script>

<style scoped>
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.search-input {
  padding: 0.5rem 1rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  width: 250px;
}

.toolbar-right {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.toolbar-right select {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
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

.price {
  color: #e94560;
  font-weight: bold;
}

.low-stock {
  color: #d9534f;
  font-weight: bold;
}

.btn-sm {
  padding: 0.25rem 0.5rem;
  font-size: 0.8rem;
  margin-right: 0.25rem;
  background: #eee;
}

.btn-danger {
  background: #d9534f;
  color: #fff;
}

.btn-danger:hover {
  background: #c9302c;
}
</style>
