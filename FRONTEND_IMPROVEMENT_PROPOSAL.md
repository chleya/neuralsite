# NeuralSite 前端改进建议书

> 编制时间: 2026-03-05
> 版本: V1.0

---

## 一、现状分析

### 1.1 当前技术栈

| 类别 | 技术 | 版本 |
|------|------|------|
| 框架 | React | 18.2.0 |
| 构建 | Vite | 5.0.0 |
| 语言 | TypeScript | 5.3.0 |
| 路由 | React Router | 6.20.0 |
| 状态 | Context API | 内置 |
| 请求 | Axios | 1.6.0 |
| 图表 | ECharts | 5.4.0 |
| 3D | Three.js | 0.160.0 |

### 1.2 当前目录结构

```
src/
├── api/client.ts          # API客户端
├── components/           # 组件
│   ├── Header.tsx
│   ├── IssueCard.tsx
│   └── ...
├── context/             # React Context
├── hooks/               # 自定义Hooks
├── pages/               # 页面
│   ├── Dashboard.tsx
│   ├── LoginPage.tsx
│   └── ...
├── services/            # 业务服务
├── styles/              # 样式
├── App.tsx
└── main.tsx
```

---

## 二、行业最佳实践对比

### 2.1 流行前端项目结构

| 项目 | 特点 |
|------|------|
| Next.js App Router | app/目录、Server Components、Layouts |
| Vite React Template | features/目录、components/、hooks/ |
| shadcn/ui | 原子化组件、composable、Radix primitives |
| TanStack Query | 数据获取、缓存、乐观更新 |

### 2.2 推荐目录结构

```
src/
├── api/                    # API层
│   ├── client.ts           # Axios实例
│   ├── endpoints/          # API端点
│   │   ├── auth.ts
│   │   ├── photos.ts
│   │   └── issues.ts
│   └── types.ts            # API类型定义
│
├── app/                    # App级配置
│   ├── App.tsx
│   ├── router.tsx         # 路由配置
│   └── providers.tsx       # Provider组合
│
├── components/            # 通用组件(原子化)
│   ├── ui/                # 基础UI组件(button/input/card)
│   ├── layout/           # 布局组件(header/sidebar)
│   └── forms/            # 表单组件
│
├── features/              # 业务功能模块(推荐)
│   ├── auth/             # 认证功能
│   │   ├── components/
│   │   ├── hooks/
│   │   └── pages/
│   ├── photos/           # 照片功能
│   └── issues/           # 问题功能
│
├── hooks/                 # 通用Hooks
│   ├── useAuth.ts
│   └── useApi.ts
│
├── lib/                   # 工具库
│   ├── utils.ts
│   └── constants.ts
│
├── styles/                # 全局样式
│   └── globals.css
│
└── types/                 # 全局类型
    └── index.ts
```

---

## 三、改进建议

### 3.1 优先级P0（必须改进）

| 问题 | 当前 | 建议 | 改进方式 |
|------|------|------|----------|
| **状态管理** | Context API | TanStack Query / Zustand | 数据获取+缓存 |
| **路由配置** | 内联switch | 独立router.tsx | 集中管理 |
| **API类型** | 无 | 生成式API类型 | 自动化 |

### 3.2 优先级P1（强烈建议）

| 问题 | 当前 | 建议 | 改进方式 |
|------|------|------|----------|
| **组件组织** | 扁平pages/ | features/目录 | 按业务模块化 |
| **样式方案** | CSS Modules | Tailwind CSS | 原子化类名 |
| **表单处理** | 手动控制 | React Hook Form | 声明式表单 |
| **UI组件库** | 自定义 | shadcn/ui | Accessible组件 |

### 3.3 优先级P2（建议改进）

| 问题 | 当前 | 建议 |
|------|------|------|
| **测试** | 无 | Vitest + React Testing Library |
| **国际化** | 无 | i18next |
| **环境配置** | 手动 | .env + Vite环境变量 |
| **代码规范** | 无 | ESLint + Prettier |

---

## 四、具体改进方案

### 4.1 状态管理改进

**当前问题:** Context API导致不必要的重渲染

**推荐方案:** TanStack Query

```typescript
// 安装
npm install @tanstack/react-query

// 使用
const { data, isLoading } = useQuery({
  queryKey: ['issues', projectId],
  queryFn: () => api.issues.list(projectId)
})
```

### 4.2 路由配置改进

**当前:** App.tsx内联路由

**建议:** 独立路由文件

```typescript
// src/app/router.tsx
import { createBrowserRouter } from 'react-router-dom'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    children: [
      { path: '/', element: <Dashboard /> },
      { path: '/issues', element: <IssueList /> },
      { path: '/photos', element: <PhotoList /> },
    ]
  },
  {
    path: '/login',
    element: <Login />
  }
])
```

### 4.3 API层改进

**当前:** 分散的API调用

**建议:** 集中式API客户端

```typescript
// src/api/client.ts
import axios from 'axios'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
})

api.interceptors.response.use(/* 错误处理 */)

// src/api/endpoints/issues.ts
export const issuesApi = {
  list: (params) => api.get('/issues', { params }),
  create: (data) => api.post('/issues', data),
  update: (id, data) => api.put(`/issues/${id}`, data),
}
```

### 4.4 组件组织改进

**当前:** src/pages/ 扁平结构

**建议:** src/features/ 功能模块

```
src/features/
├── auth/
│   ├── components/        # LoginForm, ProtectedRoute
│   ├── hooks/             # useAuth
│   └── pages/             # LoginPage, RegisterPage
├── issues/
│   ├── components/         # IssueCard, IssueList, IssueForm
│   ├── hooks/             # useIssues
│   └── pages/             # IssueListPage, IssueDetailPage
└── photos/
    ├── components/        # PhotoGrid, PhotoUploader
    └── pages/
```

---

## 五、依赖升级建议

### 5.1 当前依赖问题

| 依赖 | 问题 |
|------|------|
| react-router-dom 6.20.0 | 版本过旧 |
| axios | 建议用fetch或ky |
| echarts | 较重，可选 |

### 5.2 推荐依赖

```json
{
  "dependencies": {
    "react": "^18.3.0",
    "react-router-dom": "^7.0.0",
    "@tanstack/react-query": "^5.0.0",
    "zod": "^3.22.0",
    "react-hook-form": "^7.51.0",
    "@hookform/resolvers": "^3.3.0",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.2.0",
    "lucide-react": "^0.344.0"
  },
  "devDependencies": {
    "tailwindcss": "^3.4.0",
    "vitest": "^1.3.0",
    "@testing-library/react": "^14.2.0",
    "eslint": "^8.57.0",
    "prettier": "^3.2.0"
  }
}
```

---

## 六、实施路线图

### 第一阶段: 基础设施（1周）

- [ ] 配置ESLint + Prettier
- [ ] 配置Tailwind CSS
- [ ] 搭建TanStack Query
- [ ] 创建路由配置文件

### 第二阶段: 重构核心（2周）

- [ ] 重构API层
- [ ] 重构状态管理
- [ ] 迁移到features/结构

### 第三阶段: 组件优化（1周）

- [ ] 引入shadcn/ui
- [ ] 重构表单处理
- [ ] 添加测试

---

## 七、总结

| 维度 | 当前 | 目标 |
|------|------|------|
| 代码组织 | 扁平 | 模块化 |
| 状态管理 | Context | TanStack Query |
| 样式 | CSS Modules | Tailwind |
| 类型安全 | 部分 | 完整 |
| 可维护性 | 中 | 高 |

**总体评估:** 当前项目结构基本可用，但建议按优先级逐步改进，特别是状态管理和API层。

---

*编制单位: MiniMax Agent*
*日期: 2026-03-05*
