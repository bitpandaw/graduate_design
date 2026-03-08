<template>
  <div>
    <div class="breadcrumb">
      <router-link to="/admin/products">商品管理</router-link> / {{ isEdit ? '编辑商品' : '新增商品' }}
    </div>

    <div class="card">
      <h2>{{ isEdit ? '编辑商品' : '新增商品' }}</h2>
      <form @submit.prevent="handleSubmit">
        <div class="form-group">
          <label>商品名称</label>
          <input v-model="form.name" required placeholder="请输入商品名称" />
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>价格</label>
            <input v-model.number="form.price" type="number" step="0.01" min="0" required />
          </div>
          <div class="form-group">
            <label>库存</label>
            <input v-model.number="form.stock" type="number" min="0" required />
          </div>
        </div>
        <div class="form-group">
          <label>分类</label>
          <select v-model="form.category" required>
            <option value="">请选择分类</option>
            <option value="ELECTRONICS">电子产品</option>
            <option value="CLOTHING">服装</option>
            <option value="HOME_GOODS">家居</option>
            <option value="BOOKS">图书</option>
            <option value="SPORTS">运动</option>
          </select>
        </div>
        <div class="form-group">
          <label>商品描述</label>
          <textarea v-model="form.description" rows="4" placeholder="请输入商品描述"></textarea>
        </div>
        <div class="actions">
          <button class="btn btn-primary" type="submit" :disabled="saving">
            {{ saving ? '保存中...' : '保存' }}
          </button>
          <router-link to="/admin/products" class="btn">取消</router-link>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { productService } from '@/services/apiService'

const props = defineProps<{ id?: string }>()
const router = useRouter()
const isEdit = computed(() => !!props.id)
const saving = ref(false)

const form = reactive({
  name: '',
  price: 0,
  stock: 0,
  category: '',
  description: '',
})

onMounted(async () => {
  if (props.id) {
    try {
      const product = await productService.getProductById(Number(props.id))
      Object.assign(form, product)
    } catch (error) {
      console.error('Failed to fetch product', error)
    }
  }
})

const handleSubmit = async () => {
  saving.value = true
  try {
    if (isEdit.value && props.id) {
      await productService.updateProduct(Number(props.id), form)
    } else {
      await productService.createProduct(form)
    }
    router.push('/admin/products')
  } catch (error) {
    console.error('Failed to save product', error)
    alert('保存失败')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.breadcrumb {
  margin-bottom: 1rem;
  color: #888;
}

.breadcrumb a { color: #e94560; }

h2 { margin-bottom: 1.5rem; }

.form-group {
  margin-bottom: 1.25rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  color: #555;
  font-weight: 500;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 0.5rem 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.95rem;
}

.form-group textarea {
  resize: vertical;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.actions {
  display: flex;
  gap: 0.75rem;
  margin-top: 1rem;
}

.actions .btn:last-child {
  background: #eee;
  color: #666;
}
</style>
