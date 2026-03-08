<template>
  <div>
    <div class="toolbar">
      <input v-model="searchTerm" placeholder="搜索用户..." class="search-input" />
      <span class="count">共 {{ filteredUsers.length }} 个用户</span>
    </div>

    <div class="card">
      <table class="data-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>用户名</th>
            <th>邮箱</th>
            <th>等级</th>
            <th>余额</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in filteredUsers" :key="user.id">
            <td>{{ user.id }}</td>
            <td>{{ user.username }}</td>
            <td>{{ user.email }}</td>
            <td>
              <span class="level" :class="user.level?.toLowerCase()">{{ user.level }}</span>
            </td>
            <td>¥{{ user.balance }}</td>
            <td>
              <router-link :to="`/admin/users/${user.id}`" class="btn btn-sm">详情</router-link>
              <button class="btn btn-sm btn-danger" @click="handleDelete(user.id)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { userService } from '@/services/apiService'
import type { User } from '@/types'

const users = ref<User[]>([])
const searchTerm = ref('')

const filteredUsers = computed(() => {
  if (!searchTerm.value.trim()) return users.value
  const term = searchTerm.value.toLowerCase()
  return users.value.filter(u =>
    u.username.toLowerCase().includes(term) || u.email.toLowerCase().includes(term)
  )
})

const fetchUsers = async () => {
  try {
    users.value = await userService.getUsers()
  } catch (error) {
    console.error('Failed to fetch users', error)
  }
}

const handleDelete = async (id: number) => {
  if (!confirm('确定要删除此用户吗？')) return
  try {
    await userService.deleteUser(id)
    await fetchUsers()
  } catch (error) {
    console.error('Failed to delete user', error)
    alert('删除失败')
  }
}

onMounted(fetchUsers)
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
  font-size: 0.9rem;
  width: 250px;
}

.count {
  color: #888;
  font-size: 0.9rem;
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

.level {
  display: inline-block;
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  color: #fff;
}

.level.bronze { background-color: #cd7f32; }
.level.silver { background-color: #c0c0c0; color: #333; }
.level.gold { background-color: #ffd700; color: #333; }
.level.platinum { background-color: #e5e4e2; color: #333; }

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
