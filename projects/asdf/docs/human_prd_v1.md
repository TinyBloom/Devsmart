## 目录
- [1. 产品概述](#1-产品概述)
- [2. 功能模块](#2-功能模块)
- [3. 数据模型](#3-数据模型)
- [4. API接口](#4-api接口)
- [5. 非功能需求](#5-非功能需求)
- [6. 外部集成](#6-外部集成)
- [7. 测试计划](#7-测试计划)
- [8. 工程目录结构](#8-工程目录结构)
- [9. API响应体定义](#9-api响应体定义)
- [10. 统一错误响应格式](#10-统一错误响应格式)
- [11. 数据库建表SQL](#11-数据库建表sql)
- [12. 前端页面清单和路由定义](#12-前端页面清单和路由定义)

---

## 1. 产品概述

### 1.1 一句话描述
一款面向学校或小型组织的图书管理系统，支持管理员（Admin）上传与管理图书，学生用户在线浏览、借阅与归还图书，采用文档结构（Document Structure）存储业务数据。

### 1.2 目标用户

| 角色 | 描述 | 核心需求 |
|------|------|----------|
| 管理员（Admin） | 负责图书库存管理、用户管理与借阅监管的工作人员 | 高效上传图书、维护图书信息、查看所有借阅记录、处理逾期与异常 |
| 学生用户（Student） | 在校学生，借阅图书的主要使用者 | 快速查找图书、提交借阅申请、查看借阅状态与历史、归还图书 |

### 1.3 核心价值
- **简化流程**：将传统线下借还流程线上化，减少人工登记成本。
- **结构化数据**：使用文档结构（MongoDB 风格或 JSONB 风格）描述图书与借阅数据，灵活应对字段扩展。
- **角色权限分离**：管理员与学生用户拥有不同操作权限，确保数据安全。
- **可追溯性**：所有借还行为均生成记录，便于审计与查询。

---

## 2. 功能模块

### 2.1 模块列表

| 模块编号 | 模块名称 | 主要功能点 |
|----------|----------|------------|
| M1 | 用户认证模块 | 登录、登出、Token 管理、角色识别 |
| M2 | 图书管理模块（Admin） | 上传图书、编辑图书、删除图书、查询图书 |
| M3 | 图书浏览模块（Student） | 图书列表、图书详情、图书搜索、按分类筛选 |
| M4 | 借书模块 | 提交借书请求、查看我的借阅、借阅状态更新 |
| M5 | 还书模块 | 提交还书请求、还书确认、借阅历史查看 |
| M6 | 借阅记录管理模块（Admin） | 全量借阅记录查询、逾期提醒、强制归还 |
| M7 | 用户管理模块（Admin） | 创建学生账号、禁用/启用账号、重置密码 |

### 2.2 用户故事

| 编号 | 用户故事 | 所属模块 |
|------|----------|----------|
| US-01 | As a 管理员, I want 上传图书信息, so that 学生可以查看并借阅新书 | M2 |
| US-02 | As a 管理员, I want 编辑/删除图书, so that 保持图书库存信息准确 | M2 |
| US-03 | As a 学生用户, I want 浏览图书列表, so that 找到我感兴趣的图书 | M3 |
| US-04 | As a 学生用户, I want 查看图书详情, so that 确认图书是否符合我的需求 | M3 |
| US-05 | As a 学生用户, I want 提交借书请求, so that 借走我想要的图书 | M4 |
| US-06 | As a 学生用户, I want 查看我的借阅记录, so that 知道我有哪些书未还 | M4 |
| US-07 | As a 学生用户, I want 提交还书请求, so that 归还已借图书 | M5 |
| US-08 | As a 管理员, I want 查看所有借阅记录, so that 监管整体借阅情况 | M6 |
| US-09 | As a 管理员, I want 创建/管理学生账号, so that 管控用户访问权限 | M7 |
| US-10 | As a 用户, I want 登录系统, so that 访问对应角色功能 | M1 |

---

## 3. 数据模型

### 3.1 实体列表

#### 3.1.1 User（用户）
| 字段 | 类型 | 说明 |
|------|------|------|
| _id | ObjectId / UUID | 主键 |
| username | string | 用户名，登录凭证，唯一 |
| password_hash | string | 加密后的密码 |
| role | enum('admin', 'student') | 角色 |
| full_name | string | 真实姓名 |
| email | string | 邮箱 |
| status | enum('active', 'disabled') | 账号状态 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

#### 3.1.2 Book（图书）
| 字段 | 类型 | 说明 |
|------|------|------|
| _id | ObjectId / UUID | 主键 |
| title | string | 书名 |
| author | string | 作者 |
| isbn | string | ISBN编号，唯一 |
| category | string | 分类（如文学、科技、教材等） |
| description | string | 简介 |
| cover_url | string | 封面图片URL |
| total_copies | int | 总库存数量 |
| available_copies | int | 可借数量 |
| publisher | string | 出版社 |
| published_date | date | 出版日期 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

#### 3.1.3 BorrowRecord（借阅记录）
| 字段 | 类型 | 说明 |
|------|------|------|
| _id | ObjectId / UUID | 主键 |
| user_id | ObjectId / UUID | 借书人ID（外键关联User） |
| book_id | ObjectId / UUID | 图书ID（外键关联Book） |
| borrow_date | datetime | 借出时间 |
| due_date | datetime | 应归还时间 |
| return_date | datetime / null | 实际归还时间（未还时为null） |
| status | enum('borrowed', 'returned', 'overdue') | 状态 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

### 3.2 实体关系

```
User (1) ──────< (N) BorrowRecord >────── (N : 1) Book
```

- **User ↔ BorrowRecord**：一对多，一个用户可以有多条借阅记录。
- **Book ↔ BorrowRecord**：一对多，一本图书可以有多条借阅记录。
- **User ↔ Book**：多对多，通过 BorrowRecord 中间实体实现。

---

## 4. API接口

### 4.1 接口列表

#### 4.1.1 认证模块

| 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|
| POST | /api/v1/auth/login | 用户登录 | 公开 |
| POST | /api/v1/auth/logout | 用户登出 | 已登录 |
| GET | /api/v1/auth/me | 获取当前登录用户信息 | 已登录 |

#### 4.1.2 图书管理（Admin）

| 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|
| POST | /api/v1/admin/books | 上传/创建图书 | admin |
| PUT | /api/v1/admin/books/{id} | 更新图书信息 | admin |
| DELETE | /api/v1/admin/books/{id} | 删除图书 | admin |
| GET | /api/v1/admin/books | 查询图书列表（含筛选） | admin |

#### 4.1.3 图书浏览（Student & Admin）

| 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|
| GET | /api/v1/books | 浏览图书列表（支持分页/搜索/筛选） | 已登录 |
| GET | /api/v1/books/{id} | 获取图书详情 | 已登录 |

#### 4.1.4 借书模块

| 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|
| POST | /api/v1/borrows | 提交借书请求（传入 book_id） | student |
| GET | /api/v1/borrows/my | 获取当前用户的借阅记录 | student |

#### 4.1.5 还书模块

| 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|
| POST | /api/v1/borrows/{id}/return | 提交还书请求 | student |
| GET | /api/v1/borrows/my/history | 获取历史借阅（含已还） | student |

#### 4.1.6 借阅记录管理（Admin）

| 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|
| GET | /api/v1/admin/borrows | 查看全量借阅记录 | admin |
| PUT | /api/v1/admin/borrows/{id}/force-return | 强制归还（异常处理） | admin |

#### 4.1.7 用户管理（Admin）

| 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|
| POST | /api/v1/admin/users | 创建学生账号 | admin |
| GET | /api/v1/admin/users | 查询用户列表 | admin |
| PUT | /api/v1/admin/users/{id}/status | 启用/禁用账号 | admin |
| PUT | /api/v1/admin/users/{id}/password | 重置密码 | admin |

---

## 5. 非功能需求

### 5.1 性能要求
- 接口响应时间：P95 < 300ms，简单查询 < 100ms。
- 并发用户数：支持至少 100 并发用户同时在线。
- 列表分页接口必须支持分页参数，避免单次返回大量数据。
- 数据库关键字段（如 Book.isbn、User.username）需建立索引。

### 5.2 安全要求
- **认证方式**：采用 JWT（JSON Web Token）方案，Token 有效期 2 小时，支持 Refresh Token。
- **密码存储**：使用 bcrypt（cost factor ≥ 10）单向加密存储，禁止明文。
- **数据传输**：全站强制 HTTPS。
- **权限控制**：基于角色的访问控制（RBAC），接口层校验角色。
- **输入校验**：所有入参使用 JSON Schema 或 Pydantic 进行校验，防止注入。
- **审计日志**：所有写操作（上传/借/还/用户管理）记录审计日志。

### 5.3 扩展性要求
- 数据模型采用文档结构（Document Structure），方便后续字段扩展而无需迁移表结构。
- 后端采用分层架构（Handler/Service/Repository），便于独立扩展。
- 支持水平扩展（无状态服务 + 集中式存储）。
- 技术选型建议：
  - **后端**：Python (FastAPI) / Node.js (Express) / Go (Gin)
  - **前端**：Vue 3 + Vite / React + Vite
  - **数据库**：MongoDB（文档存储）或 PostgreSQL（JSONB 字段）

---

## 6. 外部集成

### 6.1 第三方服务

| 服务类型 | 是否需要 | 说明 |
|----------|----------|------|
| 邮件服务（SMTP） | 可选 | 用于逾期提醒、密码重置通知 |
| 文件存储（OSS） | 可选 | 用于存储图书封面图（也可本地存储） |
| ISBN 校验 API | 可选 | 用于校验 ISBN 合法性、获取图书元数据 |
| 日志服务 | 推荐 | ELK / Loki，用于集中日志分析 |
| 监控告警 | 推荐 | Prometheus + Grafana，监控接口性能与异常 |

> MVP 阶段可仅依赖本地存储与日志，第三方集成作为后续迭代项。

---

## 7. 测试计划

### 7.1 单元测试
- 针对每个核心功能模块编写单元测试。
- 覆盖正常路径、边界条件和异常路径。
- **测试文件路径**：`tests/unit/`
- 示例覆盖范围：
  - `test_auth_service.py`：登录、密码校验、Token 生成
  - `test_book_service.py`：图书 CRUD、库存扣减
  - `test_borrow_service.py`：借书/还书状态流转

### 7.2 集成测试
- 测试模块间交互、数据库读写、API 端到端调用。
- 使用测试数据库（如 MongoDB Memory Server / PostgreSQL Test DB）。
- **测试文件路径**：`tests/integration/`
- 示例覆盖范围：
  - `test_book_api.py`：完整 HTTP 请求链路
  - `test_borrow_api.py`：借还流程全链路
  - `test_auth_api.py`：登录与权限校验链路

### 7.3 端到端测试（Playwright）
- 模拟真实用户完整操作流程。
- 包含页面导航、表单填写、按钮点击、断言检查。
- **测试文件路径**：`tests/e2e/`
- 示例场景：
  - 管理员登录 → 上传图书 → 退出
  - 学生登录 → 搜索图书 → 借书 → 查看我的借阅 → 还书
  - 权限校验：学生访问 admin 接口应被拒绝

### 7.4 测试结果循环（CI 反馈机制）
- **CI 测试命令**：
  - `pytest tests/unit/ -v`
  - `pytest tests/integration/ -v`
  - `npx playwright test`
- **测试结果解析**：解析 pytest/playwright 输出，提取失败测试名称、错误信息、堆栈跟踪。
- **失败分析**：根据错误信息定位问题代码，生成修复建议。
- **代码修复**：基于失败分析结果，自动生成代码补丁（人工审核后合并）。
- **重试机制**：修复后重新运行失败的测试，最多重试 3 次。
- **循环终止条件**：所有测试通过 或 达到最大重试次数。
- **测试覆盖率要求**：单元测试覆盖率 ≥ 80%。

---

## 8. 工程目录结构

### 8.1 后端目录结构
```
backend/
├── src/
│   ├── handlers/        # HTTP 路由处理器（Controller 层）
│   │   ├── auth_handler.py
│   │   ├── book_handler.py
│   │   ├── borrow_handler.py
│   │   └── admin_handler.py
│   ├── services/        # 业务逻辑层
│   │   ├── auth_service.py
│   │   ├── book_service.py
│   │   └── borrow_service.py
│   ├── models/          # 数据模型（文档结构）
│   │   ├── user.py
│   │   ├── book.py
│   │   └── borrow_record.py
│   ├── auth/            # 认证与权限
│   │   ├── jwt_utils.py
│   │   └── decorators.py
│   ├── error/           # 统一错误处理
│   │   ├── exceptions.py
│   │   └── error_codes.py
│   ├── db/              # 数据库连接
│   │   ├── connection.py
│   │   └── repositories/
│   └── main.py          # 应用入口
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── requirements.txt
└── README.md
```

### 8.2 前端目录结构
```
frontend/
├── src/
│   ├── views/           # 页面级组件
│   │   ├── Login.vue
│   │   ├── BookList.vue
│   │   ├── BookDetail.vue
│   │   ├── MyBorrows.vue
│   │   ├── admin/
│   │   │   ├── BookManage.vue
│   │   │   ├── BorrowRecords.vue
│   │   │   └── UserManage.vue
│   ├── components/      # 通用组件
│   │   ├── BookCard.vue
│   │   ├── Pagination.vue
│   │   └── SearchBar.vue
│   ├── stores/          # 状态管理（Pinia / Vuex）
│   │   ├── user.js
│   │   └── book.js
│   ├── api/             # API 封装
│   │   ├── request.js
│   │   ├── auth.js
│   │   ├── book.js
│   │   └── borrow.js
│   ├── router/          # 路由配置
│   │   └── index.js
│   ├── utils/
│   └── main.js
├── package.json
└── vite.config.js
```

---

## 9. API响应体定义

### 9.1 分页响应格式
所有列表接口统一返回以下结构：

```json
{
  "data": [],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

### 9.2 成功响应示例

#### 9.2.1 登录成功
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": "65f0a1b2c3d4e5f6a7b8c9d0",
      "username": "student001",
      "role": "student",
      "full_name": "张三"
    }
  }
}
```

#### 9.2.2 图书列表
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "data": [
      {
        "id": "65f0a1b2c3d4e5f6a7b8c9d1",
        "title": "三体",
        "author": "刘慈欣",
        "isbn": "9787229030933",
        "category": "科幻",
        "total_copies": 5,
        "available_copies": 3
      }
    ],
    "total": 100,
    "page": 1,
    "page_size": 20
  }
}
```

#### 9.2.3 借书成功
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "borrow_id": "65f0a1b2c3d4e5f6a7b8c9d2",
    "book_id": "65f0a1b2c3d4e5f6a7b8c9d1",
    "borrow_date": "2025-01-15T10:00:00Z",
    "due_date": "2025-02-15T10:00:00Z",
    "status": "borrowed"
  }
}
```

#### 9.2.4 还书成功
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "borrow_id": "65f0a1b2c3d4e5f6a7b8c9d2",
    "return_date": "2025-01-25T14:30:00Z",
    "status": "returned"
  }
}
```

---

## 10. 统一错误响应格式

### 10.1 错误响应JSON结构
```json
{
  "code": "AUTH_INVALID_CREDENTIALS",
  "message": "用户名或密码错误",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| code | string | 业务错误码（详见错误码表） |
| message | string | 用户友好提示 |
| request_id | string | 请求唯一标识（UUID），用于日志追踪 |

#### 业务错误码示例

| 错误码 | HTTP状态码 | 含义 |
|--------|-----------|------|
| AUTH_INVALID_CREDENTIALS | 401 | 用户名或密码错误 |
| AUTH_TOKEN_EXPIRED | 401 | Token 已过期 |
| AUTH_FORBIDDEN | 403 | 无权限访问 |
| BOOK_NOT_FOUND | 404 | 图书不存在 |
| BOOK_OUT_OF_STOCK | 409 | 库存不足 |
| BOOK_ALREADY_BORROWED | 409 | 已借阅未还 |
| BORROW_NOT_FOUND | 404 | 借阅记录不存在 |
| BORROW_ALREADY_RETURNED | 409 | 已归还，无法重复操作 |
| USER_NOT_FOUND | 404 | 用户不存在 |
| VALIDATION_ERROR | 400 | 参数校验失败 |
| INTERNAL_ERROR | 500 | 服务器内部错误 |

### 10.2 HTTP状态码映射
| HTTP状态码 | 使用场景 |
|-----------|----------|
| 200 | 请求成功 |
| 201 | 资源创建成功 |
| 400 | 参数错误 / 校验失败 |
| 401 | 未认证 / Token 无效 |
| 403 | 已认证但无权限 |
| 404 | 资源不存在 |
| 409 | 资源冲突（如库存不足、重复操作） |
| 500 | 服务器内部错误 |

---

## 11. 数据库建表SQL

> 注：本项目采用文档结构存储（推荐 MongoDB），以下 SQL 仅作为关系型数据库（PostgreSQL）实现的兼容方案，使用 JSONB 字段保存文档扩展属性。

### 11.1 表结构SQL

```sql
-- 用户表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'student' CHECK (role IN ('admin', 'student')),
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'disabled')),
    extra JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 图书表
CREATE TABLE books (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    author VARCHAR(100) NOT NULL,
    isbn VARCHAR(20) NOT NULL UNIQUE,
    category VARCHAR(50) NOT NULL,
    description TEXT,
    cover_url VARCHAR(500),
    total_copies INT NOT NULL DEFAULT 0 CHECK (total_copies >= 0),
    available_copies INT NOT NULL DEFAULT 0 CHECK (available_copies >= 0),
    publisher VARCHAR(100),
    published_date DATE,
    extra JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 借阅记录表
CREATE TABLE borrow_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    book_id UUID NOT NULL,
    borrow_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    due_date TIMESTAMP NOT NULL,
    return_date TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'borrowed' CHECK (status IN ('borrowed', 'returned', 'overdue')),
    extra JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE
);
```

### 11.2 索引定义

```sql
-- 用户表索引
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_status ON users(status);

-- 图书表索引
CREATE INDEX idx_books_title ON books(title);
CREATE INDEX idx_books_author ON books(author);
CREATE INDEX idx_books_category ON books(category);
CREATE INDEX idx_books_isbn ON books(isbn);

-- 借阅记录表索引
CREATE INDEX idx_borrow_user_id ON borrow_records(user_id);
CREATE INDEX idx_borrow_book_id ON borrow_records(book_id);
CREATE INDEX idx_borrow_status ON borrow_records(status);
CREATE INDEX idx_borrow_user_status ON borrow_records(user_id, status);
CREATE INDEX idx_borrow_due_date ON borrow_records(due_date);
```

---

## 12. 前端页面清单和路由定义

### 12.1 路由列表

| 路径 | 页面组件 | 页面功能区块 | 权限 |
|------|----------|--------------|------|
| `/login` | `Login.vue` | 登录表单（用户名/密码）、角色识别跳转 | 公开 |
| `/books` | `BookList.vue` | 图书列表、搜索框、分类筛选、分页器 | 已登录 |
| `/books/:id` | `BookDetail.vue` | 图书详情、借书按钮、库存状态 | 已登录 |
| `/my/borrows` | `MyBorrows.vue` | 我的借阅记录（当前借阅/历史）、还书按钮 | student |
| `/admin/books` | `admin/BookManage.vue` | 图书列表、上传按钮、编辑/删除操作 | admin |
| `/admin/books/upload` | `admin/BookUpload.vue` | 上传图书表单（书名/作者/ISBN/封面等） | admin |
| `/admin/books/:id/edit` | `admin/BookEdit.vue` | 编辑图书表单 | admin |
| `/admin/borrows` | `admin/BorrowRecords.vue` | 全量借阅记录、筛选、强制归还 | admin |
| `/admin/users` | `admin/UserManage.vue` | 用户列表、新建用户、启禁用/重置密码 | admin |
| `/403` | `Forbidden.vue` | 无权限提示页 | 公开 |
| `/404` | `NotFound.vue` | 404 页面 | 公开 |

### 12.2 路由守卫说明
- 未登录用户访问任意受保护页面 → 重定向至 `/login`。
- 学生用户访问 `/admin/*` 路由 → 重定向至 `/403`。
- 管理员可访问所有页面（含 student 功能页面）。