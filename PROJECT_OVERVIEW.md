# 电商平台项目概览

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + TypeScript + Vite + Vue Router |
| 后端 | Java Spring Boot 微服务 + Spring Cloud Gateway |

## 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (Vue 3)                       │
│         用户前台 (/) │ 管理后台 (/admin)                     │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                 Gateway Service (:8080)                      │
│              API网关 - 路由分发                              │
└────┬────────┬────────┬────────┬────────┬────────┬───────────┘
     │        │        │        │        │        │
     ▼        ▼        ▼        ▼        ▼        ▼
┌────────┐┌────────┐┌────────┐┌────────┐┌────────┐┌────────┐
│ User   ││Product ││ Order  ││Recomm- ││ Search ││Payment │
│:8081   ││:8082   ││:8083   ││end:8084││:8085   ││:8086   │
└────────┘└────────┘└────────┘└────────┘└────────┘└────────┘
```

## 目录结构

```
market/
├── frontend/                    # 前端项目
│   └── src/
│       ├── views/
│       │   ├── user/            # 用户页面(9个)
│       │   └── admin/           # 管理页面(8个)
│       ├── layouts/             # 布局组件
│       ├── router/              # 路由配置
│       ├── services/            # API调用
│       ├── composables/         # 组合式函数
│       └── types/               # TS类型定义
│
└── backend/                     # 后端微服务
    ├── gateway-service/         # API网关
    ├── user-service/            # 用户: 注册/登录/信息
    ├── product-service/         # 商品: CRUD/库存
    ├── order-service/           # 订单: 创建/状态
    ├── recommendation-service/  # 推荐: 行为分析
    ├── search-service/          # 搜索: 商品检索
    └── payment-service/         # 支付: 订单支付
```

## 核心数据模型

```typescript
Product  { id, name, price, stock, category, description }
User     { id, username, email, level, balance, role }
Order    { id, userId, totalAmount, status, items[], createdAt }
Payment  { id, orderId, amount, status, paymentMethod }
```

## 路由概览

| 前台路由 | 后台路由 |
|---------|---------|
| / 首页 | /admin 仪表盘 |
| /products 商品列表 | /admin/products 商品管理 |
| /products/:id 商品详情 | /admin/users 用户管理 |
| /search 搜索结果 | /admin/orders 订单管理 |
| /cart 购物车* | /admin/analytics 数据分析 |
| /checkout 结算* | |
| /my-orders 我的订单* | |
| /profile 个人中心* | |

*需要登录

---

## 学习顺序

### 第一阶段: 理解整体架构
1. `frontend/src/router/index.ts` - 了解路由和页面划分
2. `backend/gateway-service/` - 了解网关路由配置
3. `frontend/src/types/index.ts` - 了解数据模型

### 第二阶段: 前端核心流程
4. `frontend/src/views/user/Home.vue` - 首页入口
5. `frontend/src/views/user/ProductBrowse.vue` - 商品浏览
6. `frontend/src/views/user/Cart.vue` → `Checkout.vue` - 购物流程
7. `frontend/src/services/apiService.ts` - API调用封装
8. `frontend/src/composables/useAuth.ts` - 认证逻辑

### 第三阶段: 后端微服务
9. `user-service/` - 用户相关(Entity→Repository→Service→Controller)
10. `product-service/` - 商品相关
11. `order-service/` - 订单相关
12. `payment-service/` - 支付相关

### 第四阶段: 进阶功能
13. `recommendation-service/` - 推荐算法
14. `search-service/` - 搜索功能
15. `frontend/src/views/admin/` - 管理后台

---

**建议**: 每个微服务按 Entity → Repository → Service → Controller 顺序阅读
