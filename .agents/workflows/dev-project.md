---
description: Agent 编写和修改项目代码的自纠流程——确保代码能运行、接口正确、与现有系统兼容
---

# 项目开发自纠 Workflow

> **// turbo-all**

## 前置：了解项目

第一次使用时读取：
- `PROJECT_OVERVIEW.md` — 系统架构和技术栈
- 当前任务涉及的具体文件

---

## 第 1 步：改之前先读懂

在修改任何文件之前，Agent 必须输出：

```
【修改前声明】
要修改的文件：[路径]
修改原因：[具体说明]
影响范围评估：
  - 直接影响：[当前文件的哪些函数/接口]
  - 间接影响：[会影响哪些其他服务/组件]
  - 接口变更：[有/无。有则说明：接口名、入参/出参变化]
潜在风险：[无 / 具体描述]
```

---

## 第 2 步：执行代码修改

写代码。

---

## 第 3 步：【强制】语法与逻辑自纠

### 3a. 静态检查

针对不同语言执行静态检查：

**Python（推荐服务）：**
// turbo
```bash
cd backend/recommendation-service/python
python -m py_compile app.py && echo "语法OK"
```

**Java（后端微服务）：**
// turbo
```bash
cd backend
mvn compile -pl <service-name> -am -q 2>&1 | tail -20
```

**Vue / TypeScript（前端）：**
// turbo
```bash
cd frontend
npx vue-tsc --noEmit 2>&1 | tail -30
```

### 3b. 检查后必须输出：

```
【静态检查报告】
✅/❌ 语法检查：[通过 / 错误信息]
✅/❌ 类型检查：[通过 / 错误信息]（适用时）

如有错误：
  错误位置：[文件:行号]
  错误原因：[分析]
  修复方案：[具体怎么改]
```

有 ❌ 必须修复后再继续，不得跳过。

---

## 第 4 步：【强制】接口兼容性自纠

修改了 API 接口（Controller、路由、请求/响应体）时必须执行：

### 4a. 找出所有调用方

```
【接口影响分析】
修改的接口：[接口路径 + HTTP方法]
原始签名：[入参/出参/状态码]
新签名：[入参/出参/状态码]

调用方检查：
  - [服务名/文件名]：[✅兼容 / ❌需要同步修改]
```

### 4b. 针对本项目的关键接口链路

| 修改位置 | 必须同步检查 |
|---|---|
| Python 推荐服务 `/recommend` | Java `RecommendationEngine.java` 调用方式 |
| Java 任意 Controller | Gateway 路由配置 + 前端 `apiService.ts` |
| 前端 `apiService.ts` | 所有使用该方法的 `.vue` 文件 |
| 数据库 Entity | Repository、Service、相关 DTO |

---

## 第 5 步：【强制】功能自纠（冒烟测试）

### 5a. Python 服务——用 curl 测试核心接口

// turbo
```bash
curl -s http://localhost:8090/health | python -m json.tool
```

```bash
curl -s -X POST http://localhost:8090/recommend \
  -H "Content-Type: application/json" \
  -d "{\"userId\":1,\"candidateProductIds\":[1,2,3,4,5],\"limit\":3}" \
  | python -m json.tool
```

### 5b. Java 服务——编译+启动检查

// turbo
```bash
cd backend && mvn package -pl <service> -am -DskipTests -q
echo "构建完成，退出码: $?"
```

### 5c. 测试后必须输出：

```
【功能测试报告】
✅/❌ 服务启动：[正常 / 报错信息]
✅/❌ 健康检查：[200 OK / 异常]
✅/❌ 核心接口：[响应符合预期 / 具体异常]
✅/❌ 响应时延：[xxms（目标<200ms）/ 超标]

发现的问题：[无 / 具体描述]
```

---

## 第 6 步：【强制】代码质量自纠

完成后，Agent 以"有经验的工程师"视角审查，输出：

```
【代码质量自评报告】
评分：[1-10分]

可读性：[✅ / ⚠️ 问题：XXX]
错误处理：[✅有异常捕获 / ❌缺少：XXX场景未处理]
边界条件：[✅已考虑空值/越界 / ❌缺少：XXX]
与现有代码风格一致：[✅ / ⚠️ 差异：XXX]
论文对应描述：[✅实现与论文描述一致 / ⚠️差异点：XXX]（毕设专项）

决定：[评分≥8 → 完成 | 评分<8 → 需改进：XXX]
```

---

## 自纠失败处理规则

| 情况 | 处理方式 |
|---|---|
| Python 语法错误 | 精确定位行号，修复后重新 `py_compile` |
| Java 编译失败 | 读取完整错误信息，逐条修复，不猜测 |
| 接口调用方不兼容 | 先修复所有调用方，再提交修改 |
| 响应时延 >200ms | 检查是否有 N+1 查询、是否需要批量推理 |
| 连续 3 次自纠失败 | 停止，向用户展示错误日志，请求人工分析 |

---

## 快速参考：各服务启动端口

| 服务 | 端口 | 语言 |
|---|---|---|
| gateway-service | 8080 | Java |
| user-service | 8081 | Java |
| product-service | 8082 | Java |
| order-service | 8083 | Java |
| recommendation-service (Java) | 8084 | Java |
| recommendation-service (Python) | 8090 | Python |
| search-service | 8085 | Java |
| payment-service | 8086 | Java |
| frontend | 5173 | Vue |
