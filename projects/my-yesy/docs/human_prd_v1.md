# my-yesy 图书管理系统 — 产品需求文档（PRD）

> 版本：v1.0  
> 适用项目：my-yesy  
> 文档状态：基于对话历史整理，部分字段已根据通用 SaaS 实践做合理默认值填充，若与你的真实需求不一致请直接修订。

---

## 目录
- [1. 产品概述](#1-产品概述)
  - [1.1 一句话描述](#11-一句话描述)
  - [1.2 目标用户](#12-目标用户)
  - [1.3 核心价值](#13-核心价值)
- [2. 功能模块](#2-功能模块)
  - [2.1 模块列表](#21-模块列表)
  - [2.2 用户故事](#22-用户故事)
- [3. 数据模型](#3-数据模型)
  - [3.1 实体列表](#31-实体列表)
  - [3.2 实体关系](#32-实体关系)
- [4. API接口](#4-api接口)
  - [4.1 接口列表](#41-接口列表)
- [5. 非功能需求](#5-非功能需求)
  - [5.1 性能要求](#51-性能要求)
  - [5.2 安全要求](#52-安全要求)
  - [5.3 扩展性要求](#53-扩展性要求)
- [6. 外部集成](#6-外部集成)
  - [6.1 第三方服务](#61-第三方服务)
- [7. 测试计划](#7-测试计划)
  - [7.1 单元测试](#71-单元测试)
  - [7.2 集成测试](#72-集成测试)
  - [7.3 端到端测试（Playwright）](#73-端到端测试playwright)
  - [7.4 测试结果循环（CI反馈机制）](#74-测试结果循环ci反馈机制)
- [8. 工程目录结构](#8-工程目录结构)
  - [8.1 后端目录结构](#81-后端目录结构)
  - [8.2 前端目录结构](#82-前端目录结构)
- [9. API响应体定义](#9-api响应体定义)
  - [9.1 分页响应格式](#91-分页响应格式)
  - [9.2 成功响应示例](#92-成功响应示例)
- [10. 统一错误响应格式](#10-统一错误响应格式)
  - [10.1 错误响应JSON结构](#101-错误响应json结构)
  - [10.2 HTTP状态码映射](#102-http状态码映射)
- [11. 数据库建表SQL](#11-数据库建表sql)
  - [11.1 表结构SQL](#111-表结构sql)
  - [11.2 索引定义](#112-索引定义)
- [12. 前端页面清单和路由定义](#12-前端页面清单和路由定义)
  - [12.1 路由列表](#121-路由列表)

---

## 1. 产品概述

### 1.1 一句话描述
my-yesy 是一款面向中小学校/学院场景的轻量级图书管理系统，支持管理员录入与维护图书资源、学生完成在线借书与还书全流程，让馆藏流通可追溯、状态可视化。

### 1.2 目标用户

| 角色 | 描述 | 核心需求 |
|------|------|---------|
| 管理员（admin） | 图书馆工作人员 / 班主任 / 系统维护者 | 录入图书、维护库存、查看借阅记录、处理归还 |
| 学生用户（student） | 在校学生，通过学号 + 密码登录 | 浏览图书、借书、还书、查询自己的借阅历史 |

> 角色互斥：一个账号只属于一种角色；通过 `role` 字段区分。

### 1.3 核心价值
- **结构化馆藏**：每本图书以「文档结构」描述其核心字段 + 扩展属性（JSON），既保留关系型字段便于检索与统计，又保留扩展字段灵活记录出版社、标签等异构信息。
- **闭环借阅流程**：借出 → 在借 → 归还，全链路留痕，可按学生、图书、时间多维查询。
- **轻量化部署**：单镜像 + 嵌入式数据库，可在 Kubernetes 单实例（StatefulSet + PVC）部署，也可在单机直接运行，便于课程/毕设场景落地。

---

## 2. 功能模块

### 2.1 模块列表

| 模块编号 | 模块名称 | 包含功能点 |
|---------|---------|-----------|
| M1 | 认证与权限 | 登录、登出、Token 刷新、当前用户信息、角色守卫 |
| M2 | 图书管理（admin） | 上传/新增、编辑、删除、批量导入、封面图片上传、库存调整 |
| M3 | 图书浏览（student） | 列表、详情、按分类筛选、关键字搜索（书名/作者/ISBN） |
| M4 | 借书（student） | 借书申请、库存校验、借阅上限校验、生成借阅记录 |
| M5 | 还书（student / admin） | 学生自助还书、admin 强制归还（处理遗失）、归还校验 |
| M6 | 借阅记录 | 我的借阅（student）、全量借阅记录查询（admin）、逾期名单 |
| M7 | 学生管理（admin） | 学生列表、冻结/解冻账号、查看单个学生借阅情况 |
| M8 | 分类管理（admin） | 图书分类 CRUD（一级分类即可） |
| M9 | 统计报表（admin） | 馆藏总数、在借数量、热门图书 Top10、逾期名单 |
| M10 | 到期提醒 | 借阅到期前 3 天站内消息提醒（v1 站内即可，邮件预留） |

### 2.2 用户故事

| 编号 | As a | I want | so that |
|------|------|--------|---------|
| US-01 | 管理员 | 新增图书并指定库存数量 | 让该书可被学生借阅 |
| US-02 | 管理员 | 编辑图书信息或调整库存 | 修正录入错误或应对丢书补书 |
| US-03 | 管理员 | 按条件查询所有借阅记录 | 定位某本书/某个学生的状态 |
| US-04 | 管理员 | 冻结某个学生账号 | 处置违规或毕业学生 |
| US-05 | 学生 | 浏览图书列表并按关键字搜索 | 快速定位想借的书 |
| US-06 | 学生 | 查看图书详情（封面、简介、可借状态） | 决定是否借阅 |
| US-07 | 学生 | 一键发起借书 | 把书借到手 |
| US-08 | 学生 | 在「我的借阅」中看到所有当前在借记录及到期日 | 不逾期 |
| US-09 | 学生 | 主动归还图书 | 结束借阅关系，释放库存 |
| US-10 | 学生 | 在到期前 3 天收到提醒 | 避免逾期 |
| US-11 | 系统 | 在借阅成功后自动扣减 `available_stock` | 保证库存数据准确 |
| US-12 | 系统 | 在归还后自动恢复 `available_stock` | 保证库存数据准确 |
| US-13 | 未登录用户 | 跳转登录页 | 完成认证后才能借书 |

> **借阅规则默认值**（如与实际不符请修改）：
> - 借阅时长：**30 天**
> - 单人同时在借上限：**5 本**
> - 是否支持续借：**v1 不支持**
> - 逾期处理：**不罚款，但限制新借阅**，直到归还所有逾期图书
> - 库存模型：**多副本模型**（一本书可有多本物理副本，独立记录可借状态）

---

## 3. 数据模型

### 3.1 实体列表

#### 3.1.1 `user`（用户表）
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | INTEGER PRIMARY KEY | 是 | 自增主键 |
| username | TEXT UNIQUE | 是 | 用户名（学生为学号） |
| password_hash | TEXT | 是 | bcrypt 哈希 |
| real_name | TEXT | 是 | 真实姓名 |
| role | TEXT | 是 | `admin` 或 `student` |
| status | TEXT | 是 | `active` / `frozen`，默认 `active` |
| email | TEXT | 否 | 邮箱（学生可选） |
| created_at | TIMESTAMP | 是 | 创建时间 |
| updated_at | TIMESTAMP | 是 | 更新时间 |

#### 3.1.2 `category`（图书分类表）
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | INTEGER PRIMARY KEY | 是 | 自增主键 |
| name | TEXT UNIQUE | 是 | 分类名，如「计算机/文学/历史」 |
| created_at | TIMESTAMP | 是 | 创建时间 |

#### 3.1.3 `book`（图书表）
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | INTEGER PRIMARY KEY | 是 | 自增主键 |
| title | TEXT | 是 | 书名 |
| author | TEXT | 是 | 作者 |
| isbn | TEXT | 是 | ISBN |
| category_id | INTEGER | 是 | 外键 → `category.id` |
| publisher | TEXT | 否 | 出版社 |
| publish_date | TEXT | 否 | 出版日期（YYYY-MM-DD） |
| price | REAL | 否 | 价格 |
| cover_url | TEXT | 否 | 封面图地址 |
| description | TEXT | 否 | 简介 |
| tags | TEXT | 否 | 标签，逗号分隔 |
| total_stock | INTEGER | 是 | 总副本数，>= 0 |
| available_stock | INTEGER | 是 | 可借副本数，0 <= available <= total |
| extra | TEXT | 否 | JSON 文档，存放扩展属性（实现「用文档结构描述数据」） |
| created_at | TIMESTAMP | 是 | 创建时间 |
| updated_at | TIMESTAMP | 是 | 更新时间 |

#### 3.1.4 `borrow_record`（借阅记录表）
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | INTEGER PRIMARY KEY | 是 | 自增主键 |
| user_id | INTEGER | 是 | 外键 → `user.id` |
| book_id | INTEGER | 是 | 外键 → `book.id` |
| borrowed_at | TIMESTAMP | 是 | 借出时间 |
| due_at | TIMESTAMP | 是 | 应还时间 |
| returned_at | TIMESTAMP | 否 | 实际归还时间，NULL 表示在借 |
| status | TEXT | 是 | `borrowing` / `returned` / `overdue` |
| operator_id | INTEGER | 否 | 若 admin 强制归还，记录操作人 |
| created_at | TIMESTAMP | 是 | 创建时间 |
| updated_at | TIMESTAMP | 是 | 更新时间 |

#### 3.1.5 `notification`（站内消息表，可选）
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | INTEGER PRIMARY KEY | 是 | 自增主键 |
| user_id | INTEGER | 是 | 外键 → `user.id` |
| type | TEXT | 是 | `due_reminder` / `overdue` / `system` |
| content | TEXT | 是 | 消息内容 |
| read | INTEGER | 是 | 0 未读 / 1 已读 |
| created_at | TIMESTAMP | 是 | 创建时间 |

### 3.2 实体关系

```
user (1) ─────< (N) borrow_record >───── (N) ───── (1) book
                                                      │
                                                      │ N
                                                      │
                                                      ▼ (1)
                                                   category

user (1) ─────< (N) notification
```

- `user` 1 → N `borrow_record`（一个学生可有多条借阅记录）
- `book` 1 → N `borrow_record`（一本书可被多人多次借）
- `category` 1 → N `book`（一个分类下多本图书）
- `user` 1 → N `notification`（一个用户多条消息）

---

## 4. API接口

> 基础路径：`/api/v1`  
> 鉴权：`Authorization: Bearer <JWT>`，除 `POST /auth/login` 与 `GET /books/**` 外均需登录。  
> 角色：路径中标注 `[admin]` 仅管理员可访问；`[student]` 仅学生可访问；未标注表示登录即可。

### 4.1 接口列表

#### M1 认证
| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| POST | `/auth/login` | 公开 | 登录，返回 JWT |
| POST | `/auth/logout` | 登录 | 登出（前端清 Token） |
| GET  | `/auth/me` | 登录 | 获取当前用户信息 |

#### M2 图书管理
| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| POST   | `/admin/books` | [admin] | 新增图书 |
| PUT    | `/admin/books/{id}` | [admin] | 编辑图书 |
| DELETE | `/admin/books/{id}` | [admin] | 删除图书（无在借时允许） |
| PATCH  | `/admin/books/{id}/stock` | [admin] | 调整库存 |
| POST   | `/admin/books/import` | [admin] | 批量导入（CSV/JSON） |
| POST   | `/admin/books/cover` | [admin] | 上传封面，返回 cover_url |

#### M3 图书浏览
| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | `/books` | 公开 | 列表（支持分页、关键字、分类筛选） |
| GET | `/books/{id}` | 公开 | 详情 |

#### M4 借书
| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| POST | `/borrows` | [student] | 发起借书，body: `{book_id}` |
| GET  | `/borrows/my` | [student] | 我的借阅（支持按状态筛选） |

#### M5 还书
| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| POST | `/borrows/{id}/return` | [student] 或 [admin] | 归还（学生只能还自己的） |
| POST | `/admin/borrows/{id}/force-return` | [admin] | 强制归还（如遗失处理） |

#### M6 借阅记录（管理）
| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | `/admin/borrows` | [admin] | 全量借阅记录查询 |
| GET | `/admin/borrows/overdue` | [admin] | 逾期名单 |

#### M7 学生管理
| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET    | `/admin/students` | [admin] | 学生列表 |
| POST   | `/admin/students` | [admin] | 新增学生 |
| PATCH  | `/admin/students/{id}/status` | [admin] | 冻结/解冻 |
| GET    | `/admin/students/{id}/borrows` | [admin] | 单个学生借阅情况 |

#### M8 分类管理
| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET    | `/categories` | 公开 | 分类列表 |
| POST   | `/admin/categories` | [admin] | 新增分类 |
| PUT    | `/admin/categories/{id}` | [admin] | 编辑分类 |
| DELETE | `/admin/categories/{id}` | [admin] | 删除分类（无关联图书时） |

#### M9 统计报表
| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | `/admin/stats/overview` | [admin] | 馆藏总数、在借数、逾期数 |
| GET | `/admin/stats/popular` | [admin] | 热门图书 Top10 |

#### M10 消息
| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET  | `/notifications/my` | 登录 | 我的消息 |
| PATCH | `/notifications/{id}/read` | 登录 | 标记已读 |

---

## 5. 非功能需求

### 5.1 性能要求
- 单次 API 响应 P95 ≤ 300ms（不包含批量导入）。
- 图书列表查询支持分页，默认 `page=1, page_size=20`，最大 `page_size=100`。
- 借书接口需保证原子性（事务），避免超扣库存。
- 系统支持 ≥ 50 并发用户（学生同时操作）无明显卡顿（课程/毕设规模）。

### 5.2 安全要求
- 密码使用 **bcrypt** 哈希存储，禁止明文。
- 鉴权采用 **JWT**，有效期 2 小时，支持 Refresh Token（7 天）。
- 所有 `/admin/**` 接口必须有角色校验。
- SQL 注入：使用 JPA / 参数化查询，禁止拼接 SQL。
- XSS：前端对用户输入展示做转义；后端存储不做过滤。
- CORS：仅允许配置的域名跨域。
- 文件上传：封面图片大小 ≤ 2MB，类型限制 `jpg/png/webp`。
- 敏感接口（登录、修改密码）需要做限流（建议每 IP 每分钟 30 次）。

### 5.3 扩展性要求
- 后端使用 **Spring Boot 3.x + Spring Data JPA**，便于后续切换数据库。
- 数据访问层（Repository）与业务层（Service）解耦。
- 前端使用 **Vue 3 + Vite + Pinia + Vue Router**，组件化设计。
- 「文档结构描述数据」通过 `book.extra` JSON 字段实现（SQLite ≥ 3.38 支持 JSON 函数），后续可平滑迁移到 PostgreSQL 的 `JSONB`。
- 数据库部署建议：**StatefulSet + PVC 单实例**（适用于课程/毕设），部署文档需注明后续可平滑迁移到 PostgreSQL。
- 前后端分离部署：前端静态资源构建后由 Nginx 提供，后端为独立 Spring Boot 镜像。

---

## 6. 外部集成

### 6.1 第三方服务

| 服务 | 用途 | 是否必需 | 说明 |
|------|------|---------|------|
| SQLite 数据库 | 数据持久化 | 必需 | 嵌入式数据库，单文件 |
| 文件存储（本地） | 存放图书封面 | 必需 v1 | 存到后端挂载卷的 `/data/covers/`，返回 URL |
| 对象存储（OSS/S3） | 后续扩展封面存储 | 否，预留接口 | v1 不集成，封面存储抽象成 `StorageService` 接口 |
| 邮件服务（SMTP） | 借阅到期提醒 | 可选 | v1 用站内消息；如需邮件，预留 `EmailService` 接口 |
| Swagger / SpringDoc | API 文档 | 推荐 | 自动生成 OpenAPI 3 文档 |
| JWT 库（jjwt） | 鉴权 | 必需 | 无状态 Token |

---

## 7. 测试计划

### 7.1 单元测试
- **覆盖范围**：Service 层 + Util 工具类。
- **覆盖目标**：单元测试覆盖率 **≥ 80%**。
- **测试内容**：
  - 借书业务正常路径（库存充足、未逾期、未达上限）。
  - 借书异常路径：库存不足、达到借阅上限、有逾期未还、账号冻结。
  - 还书业务：正常归还、强制归还、不属于自己的记录拒绝。
  - 库存增减原子性。
  - 密码哈希与校验。
  - JWT 生成与解析。
- **技术栈**：JUnit 5 + Mockito。
- **测试文件路径**：`backend/src/test/java/com/myyesy/**/*Test.java`（Maven 标准结构）。

### 7.2 集成测试
- **覆盖范围**：Controller → Service → Repository → DB（使用内存 SQLite 或 Testcontainers）。
- **测试内容**：
  - 各接口 HTTP 状态码与响应体。
  - 借书 → 在借记录查询 → 还书 → 库存恢复 完整链路。
  - 角色权限：admin / student 接口越权访问返回 403。
  - 分页参数边界。
  - JWT 鉴权缺失/过期返回 401。
- **测试文件路径**：`backend/src/test/java/com/myyesy/integration/**/*IT.java`。

### 7.3 端到端测试（Playwright）
- **覆盖范围**：前端关键用户流程。
- **测试场景**：
  - 学生登录 → 浏览图书 → 搜索 → 借书 → 我的借阅查看 → 还书。
  - 管理员登录 → 新增分类 → 新增图书 → 查看借阅列表 → 强制归还。
  - 未登录访问受保护页面跳转登录。
  - 表单校验（空字段、超长输入）。
- **测试文件路径**：`frontend/tests/e2e/*.spec.ts`。

### 7.4 测试结果循环（CI反馈机制）

```
┌─────────────────────────────────────────────────────────────┐
│  CI Test Pipeline with Auto-Retry                           │
├─────────────────────────────────────────────────────────────┤
│  1. 运行测试                                                 │
│     - pytest tests/unit/ -v                                  │
│     - pytest tests/integration/ -v                           │
│     - npx playwright test                                    │
│                                                             │
│  2. 解析测试结果                                              │
│     - 提取失败的测试名称、错误信息、堆栈跟踪                    │
│     - 分类：断言失败 / 异常 / 超时                            │
│                                                             │
│  3. 失败分析                                                 │
│     - 根据错误信息定位问题代码                                 │
│     - 生成修复建议                                            │
│                                                             │
│  4. 代码修复                                                 │
│     - 基于失败分析结果，自动生成代码补丁                       │
│                                                             │
│  5. 重试机制                                                 │
│     - 修复后重新运行失败的测试                                 │
│     - 最多重试 3 次                                          │
│                                                             │
│  6. 循环终止条件                                              │
│     - ✓ 所有测试通过                                         │
│     - ✗ 达到最大重试次数 (3)，上报人工处理                    │
└─────────────────────────────────────────────────────────────┘
```

- **测试覆盖率要求**：单元测试覆盖率 **≥ 80%**。
- **CI 触发**：GitHub Actions，PR 与 main 分支 push 时执行。

---

## 8. 工程目录结构

### 8.1 后端目录结构

```
backend/
├── src/
│   ├── main/
│   │   ├── java/com/myyesy/
│   │   │   ├── MyYesyApplication.java          # 启动类
│   │   │   ├── config/                          # 配置类
│   │   │   │   ├── SecurityConfig.java
│   │   │   │   ├── CorsConfig.java
│   │   │   │   └── SwaggerConfig.java
│   │   │   ├── controller/                      # 控制器层（API 入口）
│   │   │   │   ├── AuthController.java
│   │   │   │   ├── BookController.java
│   │   │   │   ├── AdminBookController.java
│   │   │   │   ├── BorrowController.java
│   │   │   │   ├── AdminBorrowController.java
│   │   │   │   ├── AdminStudentController.java
│   │   │   │   ├── CategoryController.java
│   │   │   │   ├── AdminCategoryController.java
│   │   │   │   ├── AdminStatsController.java
│   │   │   │   └── NotificationController.java
│   │   │   ├── service/                         # 业务逻辑层
│   │   │   │   ├── AuthService.java
│   │   │   │   ├── BookService.java
│   │   │   │   ├── BorrowService.java
│   │   │   │   ├── CategoryService.java
│   │   │   │   ├── StudentService.java
│   │   │   │   ├── StatsService.java
│   │   │   │   └── NotificationService.java
│   │   │   ├── repository/                      # 数据访问层
│   │   │   │   ├── UserRepository.java
│   │   │   │   ├── BookRepository.java
│   │   │   │   ├── BorrowRecordRepository.java
│   │   │   │   ├── CategoryRepository.java
│   │   │   │   └── NotificationRepository.java
│   │   │   ├── model/                           # 实体类（JPA Entity）
│   │   │   │   ├── User.java
│   │   │   │   ├── Book.java
│   │   │   │   ├── BorrowRecord.java
│   │   │   │   ├── Category.java
│   │   │   │   └── Notification.java
│   │   │   ├── dto/                             # 数据传输对象
│   │   │   │   ├── request/
│   │   │   │   │   ├── LoginRequest.java
│   │   │   │   │   ├── CreateBookRequest.java
│   │   │   │   │   ├── BorrowRequest.java
│   │   │   │   │   └── ...
│   │   │   │   └── response/
│   │   │   │       ├── LoginResponse.java
│   │   │   │       ├── BookResponse.java
│   │   │   │       └── ...
│   │   │   ├── auth/                            # 鉴权相关
│   │   │   │   ├── JwtTokenProvider.java
│   │   │   │   ├── JwtAuthFilter.java
│   │   │   │   └── UserPrincipal.java
│   │   │   ├── exception/                       # 自定义异常
│   │   │   │   ├── BusinessException.java
│   │   │   │   ├── ResourceNotFoundException.java
│   │   │   │   └── GlobalExceptionHandler.java
│   │   │   └── util/
│   │   │       ├── PageUtil.java
│   │   │       └── DateUtil.java
│   │   └── resources/
│   │       ├── application.yml
│   │       ├── application-dev.yml
│   │       ├── application-prod.yml
│   │       └── db/
│   │           └── migration/                   # Flyway 迁移脚本
│   │               └── V1__init_schema.sql
│   └── test/
│       └── java/com/myyesy/
│           ├── unit/
│           └── integration/
├── pom.xml
└── Dockerfile
```

### 8.2 前端目录结构

```
frontend/
├── src/
│   ├── views/                                   # 页面组件
│   │   ├── auth/
│   │   │   └── LoginView.vue
│   │   ├── student/
│   │   │   ├── BookListView.vue
│   │   │   ├── BookDetailView.vue
│   │   │   ├── MyBorrowsView.vue
│   │   │   └── NotificationsView.vue
│   │   ├── admin/
│   │   │   ├── AdminDashboardView.vue
│   │   │   ├── BookManageView.vue
│   │   │   ├── BookFormView.vue
│   │   │   ├── BorrowRecordsView.vue
│   │   │   ├── StudentManageView.vue
│   │   │   ├── CategoryManageView.vue
│   │   │   └── StatsView.vue
│   │   ├── ErrorView.vue
│   │   └── NotFoundView.vue
│   ├── components/                              # 通用组件
│   │   ├── BookCard.vue
│   │   ├── BookTable.vue
│   │   ├── Pagination.vue
│   │   ├── SearchBar.vue
│   │   ├── NavBar.vue
│   │   └── SideBar.vue
│   ├── stores/                                  # Pinia 状态管理
│   │   ├── auth.ts
│   │   ├── book.ts
│   │   ├── borrow.ts
│   │   └── notification.ts
│   ├── api/                                     # API 客户端
│   │   ├── request.ts                           # axios 实例
│   │   ├── auth.ts
│   │   ├── book.ts
│   │   ├── borrow.ts
│   │   ├── admin.ts
│   │   └── notification.ts
│   ├── router/
│   │   └── index.ts                             # 路由配置
│   ├── types/                                   # TypeScript 类型定义
│   │   ├── book.ts
│   │   ├── user.ts
│   │   ├── borrow.ts
│   │   └── api.ts
│   ├── utils/
│   │   ├── auth.ts
│   │   ├── format.ts
│   │   └── validate.ts
│   ├── App.vue
│   └── main.ts
├── tests/
│   └── e2e/
│       ├── student-flow.spec.ts
│       ├── admin-flow.spec.ts
│       └── auth.spec.ts
├── public/
├── index.html
├── vite.config.ts
├── tsconfig.json
├── package.json
└── Dockerfile
```

---

## 9. API响应体定义

### 9.1 分页响应格式

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "items": [ ... ],
    "total": 128,
    "page": 1,
    "page_size": 20,
    "total_pages": 7
  },
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 9.2 成功响应示例

#### 9.2.1 登录成功
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiJ9...",
    "token_type": "Bearer",
    "expires_in": 7200,
    "user": {
      "id": 12,
      "username": "2023001",
      "real_name": "张三",
      "role": "student",
      "email": "zhangsan@school.edu"
    }
  },
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### 9.2.2 图书列表
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "items": [
      {
        "id": 1,
        "title": "深入理解计算机系统",
        "author": "Randal E. Bryant",
        "isbn": "9787111321330",
        "category": { "id": 1, "name": "计算机" },
        "cover_url": "/data/covers/9787111321330.jpg",
        "description": "本书从程序员的视角详细阐述计算机系统的本质概念。",
        "publisher": "机械工业出版社",
        "publish_date": "2011-01-01",
        "price": 99.00,
        "tags": ["计算机", "经典", "教材"],
        "total_stock": 5,
        "available_stock": 3,
        "extra": { "language": "zh", "pages": 800, "edition": "3" }
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20,
    "total_pages": 1
  },
  "request_id": "..."
}
```

#### 9.2.3 借书成功
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "borrow_id": 1001,
    "book_id": 1,
    "book_title": "深入理解计算机系统",
    "borrowed_at": "2025-01-15T10:30:00Z",
    "due_at": "2025-02-14T10:30:00Z",
    "status": "borrowing",
    "remaining_quota": 4
  },
  "request_id": "..."
}
```

#### 9.2.4 我的借阅
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "items": [
      {
        "id": 1001,
        "book": {
          "id": 1,
          "title": "深入理解计算机系统",
          "cover_url": "/data/covers/9787111321330.jpg"
        },
        "borrowed_at": "2025-01-15T10:30:00Z",
        "due_at": "2025-02-14T10:30:00Z",
        "returned_at": null,
        "status": "borrowing",
        "overdue_days": 0
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20,
    "total_pages": 1
  },
  "request_id": "..."
}
```

#### 9.2.5 统计概览
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "total_books": 1280,
    "total_copies": 3500,
    "available_copies": 2850,
    "borrowing_count": 620,
    "overdue_count": 30,
    "active_students": 480
  },
  "request_id": "..."
}
```

---

## 10. 统一错误响应格式

### 10.1 错误响应JSON结构