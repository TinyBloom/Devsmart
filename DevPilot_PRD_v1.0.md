# Product Requirements Document
# DevSmart - AI-Powered Software Development Platform

**Version:** 1.1  
**Status:** Active Development  
**Last Updated:** 2026-07-15  
**Document Type:** Human-readable PRD（供人审阅）

---

## 目录

1. [产品概述](#1-产品概述)
2. [核心理念与设计原则](#2-核心理念与设计原则)
3. [系统架构总览](#3-系统架构总览)
   - [3.1 RAG 三层记忆架构](#31-rag-三层记忆架构)
4. [用户角色](#4-用户角色)
5. [功能模块详述](#5-功能模块详述)
   - Phase 0: 项目管理（含模板向导）
   - Phase 1: 需求澄清与 PRD 生成（含下载）
   - Phase 2: 技术选型
   - Phase 3: 页面原型设计
   - Phase 4: 工程脚手架与代码生成
   - Phase 5: 测试生成与自动修复
   - Phase 6: 部署配置生成
6. [Skill 系统设计](#6-skill-系统设计)
7. [状态管理机制](#7-状态管理机制)
8. [非功能需求](#8-非功能需求)
9. [技术栈约束](#9-技术栈约束)
   - [9.3 数据库迁移说明](#93-数据库迁移说明)
10. [里程碑计划](#10-里程碑计划)
11. [附录：Machine-readable PRD Schema](#11-附录machine-readable-prd-schema)
12. [LLM 执行指南（Execution Guide）](#12-llm-执行指南execution-guide)

---

## 1. 产品概述

### 1.1 产品名称

**DevSmart** — AI 驱动的软件产品全生命周期生成平台

### 1.2 产品定位

DevSmart 是一个面向开发者和产品经理的 AI-Native 需求分析与 PRD 生成平台。用户通过自然语言描述想法，平台通过 LLM 对话引导，生成高质量的产品需求文档（PRD），并提供下载功能。下载后的 PRD 文档可交给任何 Code Agent（如 DevInfra、Cursor、GitHub Copilot 等）来生成代码。

**当前版本定位：**
- **核心功能**：需求澄清、PRD 生成、PRD 下载
- **输出交付物**：Human PRD（Markdown）、Machine PRD（YAML）
- **后续流程**：下载的 PRD 可作为输入交付给任何 Code Agent 进行代码生成

### 1.3 核心价值主张

> 从一句话想法，到结构化需求文档，全程 AI 辅助，PRD 可被任何 Code Agent 消费。

### 1.4 产品边界（Scope）

**当前版本（Phase 1 完成）包含：**
- 需求澄清与结构化 PRD 生成
- 技术栈选择（通过模板向导）
- PRD 下载（Human PRD + Machine PRD）
- 项目管理（创建、列表、恢复）

**后续版本规划（Phase 2-6）：**
- 页面原型生成（HTML 静态原型）
- 工程脚手架生成
- 完整代码生成（逐模块）
- 测试代码生成（Unit / Integration / E2E）
- 本地测试执行与 LLM 自动修复
- 部署配置生成（K8s Helm / Go Operator / Spring Cloud）

**不包含：**
- 云资源的实际申请和购买
- 生产环境的直接部署执行（只生成配置）
- 设计稿级别的 UI（非 Figma 精度）
- 数据库运维和监控

---

## 2. 核心理念与设计原则

### 2.1 人机协作分工

| 谁来做 | 做什么 |
|---|---|
| 用户 | 描述需求、做选择题、确认产出 |
| LLM | 追问补全、生成代码、修复错误 |
| Skill | 执行固定流程、验证产出、格式转换 |

### 2.2 两种 PRD 并存

平台维护同一份信息的两个版本：

- **Human PRD**（Markdown）：供用户阅读、确认、存档
- **Machine PRD**（YAML）：供所有 Skill 程序化消费，用户不直接接触

用户只操作 Human PRD；YAML 由平台自动生成和维护。

### 2.3 TDD 优先

代码生成顺序为：接口契约 → 测试代码 → 实现代码。先写测试再写实现，保证代码质量。

### 2.4 逐模块生成

不一次性生成全部代码。每次 LLM 上下文只聚焦一个模块，保证生成质量和一致性。

### 2.5 反馈循环

测试失败时，平台自动将错误信息喂给 LLM，最多重试 N 次（默认 3 次），超出则转人工。

### 2.6 状态驱动

平台通过一个中央状态文件（`project.json`）追踪当前阶段和各模块完成情况，每个 Skill 读状态、执行、更新状态。

---

## 3. 系统架构总览

```
┌─────────────────────────────────────────────────────────────┐
│                        Web Frontend                          │
│              TypeScript + React + Vite                        │
│      对话界面 / 项目列表 / 模板向导 / PRD预览 / 下载        │
└───────────────────────┬─────────────────────────────────────┘
                        │ REST API
┌───────────────────────▼─────────────────────────────────────┐
│                     Python Backend                            │
│                   FastAPI + SQLAlchemy                        │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │  LLM Gateway │  │ Skill Engine │  │  Project Manager  │  │
│  │  （适配层）  │  │  （执行器）  │  │  （状态管理）     │  │
│  └──────┬───────┘  └──────┬───────┘  └────────┬──────────┘  │
│         │                 │                    │              │
│  ┌──────▼─────────────────▼────────────────────▼──────────┐  │
│  │                   Core Services                         │  │
│  │  对话服务 / PRD服务 / RAG服务 / 摘要服务                │  │
│  └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                    External LLM APIs                          │
│         OpenAI / Anthropic / Google / 本地 Ollama            │
└─────────────────────────────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                   Storage Layer                               │
│      SQLite（项目数据）+ ChromaDB（向量数据库）              │
│      本地文件系统（生成的代码 / PRD / 原型）                 │
└─────────────────────────────────────────────────────────────┘
```

### 3.1 RAG 三层记忆架构

平台引入 RAG（Retrieval-Augmented Generation）技术，构建三层记忆架构，提升对话上下文理解能力：

| 层级 | 内容 | 存储方式 | 检索方式 |
|------|------|---------|---------|
| **短期记忆** | 当前对话历史（最近 5-10 轮） | SQLite | 直接读取 |
| **中期记忆** | 对话摘要、关键决策点 | ChromaDB | 相似度检索 |
| **长期记忆** | 模板数据、PRD、技术文档、代码规范 | ChromaDB | 语义检索 |

**工作机制：**

1. **长期记忆**：项目创建时，模板数据（需求描述、技术选型、部署形式）自动存入向量数据库。每次对话时，根据用户输入进行语义检索，将相关的项目知识注入到 LLM 上下文。

2. **中期记忆**：对话过程中定期生成摘要，摘要内容存入向量数据库。检索时通过相似度匹配，找到与当前话题相关的历史对话要点。

3. **短期记忆**：最近 N 轮对话直接从数据库读取，确保上下文的连续性。

**降级策略：**
- 当 RAG 服务不可用时（如向量数据库未初始化、网络问题），系统自动降级为传统的系统提示注入方式，使用项目的 `onboarding_data` 作为系统提示。

---

## 4. 用户角色

平台不设用户注册/登录/权限管理，只有单一角色：**操作者**。

### 4.1 操作者

- 直接使用平台创建和管理项目
- 通过项目名称进入/恢复工作
- 对所有项目拥有完全控制权
- 可以是产品经理、开发者或任何有软件想法的人

---

## 5. 功能模块详述

---

### Phase 0：项目管理

#### 5.0.1 功能描述

用户进入平台后，首先看到项目列表。可以创建新项目或选择已有项目继续工作。项目是平台的核心入口，所有后续操作都围绕项目展开。

#### 5.0.2 流程

```
打开平台首页
    ↓
展示项目列表（可搜索）
    ↓
[新建项目] → 填写模板向导（需求描述、技术选型、部署形式） → 进入 Phase 1 对话
[选择已有项目] → 恢复到上次中断的位置继续
```

#### 5.0.3 项目列表展示字段

| 字段 | 说明 |
|---|---|
| 项目名称 | 用户输入的名字（唯一标识） |
| 当前阶段 | Phase 0-6 + 状态（pending/in_progress/completed） |
| 最后修改时间 | 上次操作时间 |
| PRD 版本 | 当前是第几版 |

#### 5.0.4 项目创建规则

- 项目名称必须唯一
- 项目名称只能包含字母、数字、下划线、连字符
- 项目名称长度 3-64 个字符
- 创建项目时自动生成 `project.json` 初始状态文件

#### 5.0.5 项目恢复机制

选择已有项目后：
1. 读取 `project.json` 获取当前阶段和状态
2. 读取对话历史（最近 N 轮 + 摘要）
3. 读取最新版本的 PRD
4. 恢复到上次中断的界面继续工作

#### 5.0.6 API 接口定义

**项目管理接口：**

| 接口 | 方法 | 路径 | 说明 |
|---|---|---|---|
| 创建项目 | POST | /api/projects | 创建新项目 |
| 获取项目列表 | GET | /api/projects | 获取所有项目（支持搜索） |
| 获取项目详情 | GET | /api/projects/{name} | 获取项目详情和当前状态 |
| 更新项目 | PUT | /api/projects/{name} | 更新项目信息 |
| 删除项目 | DELETE | /api/projects/{name} | 删除项目（含所有关联数据） |

**请求体格式（创建项目）：**

```json
{
  "name": "my-todo-app",
  "description": "一个任务管理应用",
  "onboarding_data": {
    "requirements": "一个任务管理应用，支持任务创建、分配、进度追踪",
    "tech_stack": {
      "backend": "python",
      "frontend": "react",
      "database": "postgresql"
    },
    "deployment": "local_docker"
  }
}
```

**响应体格式：**

```json
{
  "id": "uuid",
  "name": "my-todo-app",
  "description": "一个任务管理应用",
  "current_phase": "prd",
  "prd_version": 0,
  "created_at": "2026-06-28T10:00:00Z",
  "updated_at": "2026-06-28T10:00:00Z"
}
```

**模板向导字段说明：**

| 字段 | 类型 | 说明 |
|---|---|---|
| requirements | string | 需求描述，用户通过自然语言描述项目需求 |
| tech_stack.backend | string | 后端技术选型（python / java / go / rust） |
| tech_stack.frontend | string | 前端技术选型（react / vue / typescript） |
| tech_stack.database | string | 数据库选型（postgresql / mysql / sqlite / mongodb） |
| deployment | string | 部署形式（local_docker / k8s_helm / spring_cloud） |

---

### Phase 1：需求澄清与 PRD 生成

#### 5.1.1 功能描述

用户在对话界面输入初步想法，LLM 通过多轮对话追问，逐步补全需求细节，直到需求达到足够完整度，输出双版本 PRD。

#### 5.1.2 对话流程

```
用户输入初步想法
    ↓
LLM 分析缺失维度（功能/用户/数据/规模/集成）
    ↓
LLM 追问（每次只问一个问题，避免用户压力）
    ↓
用户回答
    ↓
平台计算需求完整度分数（0-100）
    ↓
[分数 < 80] → 继续追问
[分数 ≥ 80] → 提示用户确认进入生成
    ↓
生成 Human PRD（Markdown）
    ↓
用户确认 / 修改
    ↓
生成 Machine PRD（YAML）
    ↓
更新 project.json，Phase 1 完成
```

#### 5.1.3 需求完整度评分维度

| 维度 | 权重 | 说明 | 检测关键词 |
|---|---|---|---|
| 核心功能是否明确 | 30% | 有哪些主要功能模块 | 功能、模块、feature、用户故事 |
| 用户角色是否定义 | 15% | 谁在使用这个系统 | 用户、角色、admin、user、customer |
| 数据实体是否明确 | 25% | 核心数据模型有哪些字段 | 数据、实体、表、字段、model |
| 非功能需求 | 15% | 并发量、安全要求、性能要求 | 并发、性能、安全、响应时间 |
| 外部集成 | 15% | 是否需要对接第三方服务 | 集成、API、第三方、支付、邮件 |

#### 5.1.4 Skill：`skill_prd_generate`

**输入：** 对话历史（JSON）  
**输出：**
- `human_prd.md`：人类可读 PRD
- `machine_prd.yaml`：机器可读 PRD（见第 11 节 Schema）

**触发时机：** 需求完整度 ≥ 80 且用户确认

#### 5.1.5 Human PRD 模板结构

```
# 项目名称

## 1. 产品概述
   - 一句话描述
   - 目标用户
   - 核心价值

## 2. 功能模块
   - 模块名称
   - 功能列表
   - 用户故事（As a ... I want ... So that ...）

## 3. 数据模型
   - 实体名称
   - 字段列表（名称 / 类型 / 是否必填）
   - 实体关系

## 4. API 接口清单
   - 接口路径
   - 方法
   - 权限

## 5. 非功能需求
   - 性能要求
   - 安全要求
   - 扩展性要求

## 6. 外部集成
   - 第三方服务列表
```

#### 5.1.6 API 接口定义

**对话管理接口：**

| 接口 | 方法 | 路径 | 说明 |
|---|---|---|---|
| 创建会话 | POST | /api/conversations | 创建新的对话会话 |
| 获取会话列表 | GET | /api/conversations | 获取用户所有会话 |
| 获取会话详情 | GET | /api/conversations/{id} | 获取单个会话的完整对话历史 |
| 发送消息 | POST | /api/conversations/{id}/messages | 用户发送消息，触发 LLM 回复 |
| 删除会话 | DELETE | /api/conversations/{id} | 删除会话 |

**请求体格式：**

```json
{
  "content": "我想做一个任务管理应用",
  "type": "user"
}
```

**响应体格式：**

```json
{
  "id": "uuid",
  "conversation_id": "uuid",
  "content": "好的，我来帮你梳理需求。首先，这个任务管理应用的核心用户是谁？",
  "type": "assistant",
  "timestamp": "2026-06-28T10:00:00Z",
  "completeness_score": 25
}
```

**PRD 生成接口：**

| 接口 | 方法 | 路径 | 说明 |
|---|---|---|---|
| 生成 PRD | POST | /api/prd/generate | 基于对话历史生成双版本 PRD |
| 获取 PRD | GET | /api/prd/{project_id} | 获取已生成的 PRD |

**请求体格式：**

```json
{
  "conversation_id": "uuid",
  "project_name": "my-todo-app"
}
```

**响应体格式：**

```json
{
  "status": "success",
  "human_prd_path": "docs/human_prd.md",
  "machine_prd_path": "docs/machine_prd.yaml",
  "project_id": "uuid"
}
```

#### 5.1.7 数据模型定义

**SQLite 表结构：**

**projects 表：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| id | UUID | 是 | 主键 |
| name | string | 是 | 项目名称（唯一） |
| description | string | 否 | 项目描述 |
| current_phase | string | 是 | 当前阶段（prd/tech/prototype/scaffold/code/test/deploy） |
| prd_version | int | 是 | 当前 PRD 版本号 |
| onboarding_data | JSON | 否 | 模板向导数据（需求描述、技术选型、部署形式） |
| created_at | datetime | 是 | 创建时间 |
| updated_at | datetime | 是 | 更新时间 |

**conversations 表：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| id | UUID | 是 | 主键 |
| project_id | UUID | 是 | 关联项目 ID（FK） |
| phase | string | 是 | 所属阶段 |
| role | string | 是 | user / assistant / system |
| content | text | 是 | 消息内容 |
| token_count | int | 是 | 该消息的 token 数 |
| completeness_score | float | 否 | 当前完整度评分 |
| created_at | datetime | 是 | 创建时间 |

**conversation_summaries 表：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| id | UUID | 是 | 主键 |
| project_id | UUID | 是 | 关联项目 ID（FK） |
| phase | string | 是 | 所属阶段 |
| summary | text | 是 | LLM 生成的摘要 |
| covers_up_to_id | UUID | 是 | 摘要覆盖到哪条消息（FK → conversations.id） |
| created_at | datetime | 是 | 创建时间 |

**document_versions 表：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| id | UUID | 是 | 主键 |
| project_id | UUID | 是 | 关联项目 ID（FK） |
| doc_type | string | 是 | human_prd / machine_prd / pages_spec / openapi / schema |
| version | int | 是 | 版本号 |
| content | text | 是 | 文档内容 |
| change_summary | string | 否 | 这次改了什么 |
| created_at | datetime | 是 | 创建时间 |

**RAG 向量数据库（ChromaDB）：**

RAG 数据存储在 ChromaDB 向量数据库中，不存储在 SQLite：

| Collection | 用途 | 字段 |
|---|---|---|
| long_term | 长期记忆（模板数据、PRD、技术文档） | project_id, content, metadata |
| medium_term | 中期记忆（对话摘要、关键决策点） | project_id, content, metadata |

**本地文件系统结构：**

```
projects/
└── {project_name}/
    ├── project.json
    ├── docs/
    │   ├── human_prd_v1.md
    │   ├── human_prd_v2.md
    │   ├── human_prd_current.md
    │   ├── machine_prd_v1.yaml
    │   ├── machine_prd_v2.yaml
    │   └── machine_prd_current.yaml
    ├── backend/
    ├── frontend/
    └── deploy/
```

#### 5.1.8 LLM 追问策略

LLM 必须按照以下优先级顺序追问：

```
1. 核心功能 → 2. 用户角色 → 3. 数据实体 → 4. 非功能需求 → 5. 外部集成
```

**追问示例：**

| 当前缺失维度 | 追问示例 |
|---|---|
| 核心功能 | "你提到要做一个任务管理应用，请问它的核心功能有哪些？比如任务创建、分配、进度追踪等。" |
| 用户角色 | "这个应用的目标用户是谁？比如个人用户、团队成员、管理员等。" |
| 数据实体 | "你提到了任务，请问任务有哪些属性？比如标题、描述、状态、优先级等。" |
| 非功能需求 | "这个应用预期有多少用户同时使用？对响应时间有什么要求？" |
| 外部集成 | "是否需要集成其他服务？比如邮件通知、日历同步、第三方登录等。" |

#### 5.1.9 完整度评分算法实现

```python
class CompletenessService:
    def calculate(self, conversation_history):
        scores = {
            "core_features": self._evaluate_dimension(conversation_history, ["功能", "模块", "feature", "用户故事", "功能点"]),
            "user_roles": self._evaluate_dimension(conversation_history, ["用户", "角色", "admin", "user", "customer", "用户类型"]),
            "data_entities": self._evaluate_dimension(conversation_history, ["数据", "实体", "表", "字段", "model", "属性", "字段名"]),
            "non_functional": self._evaluate_dimension(conversation_history, ["并发", "性能", "安全", "响应时间", "QPS", "可用性"]),
            "integrations": self._evaluate_dimension(conversation_history, ["集成", "API", "第三方", "支付", "邮件", "对接"])
        }
        
        weights = {
            "core_features": 0.3,
            "user_roles": 0.15,
            "data_entities": 0.25,
            "non_functional": 0.15,
            "integrations": 0.15
        }
        
        total = sum(scores[key] * weights[key] for key in scores)
        return round(total, 2)
    
    def _evaluate_dimension(self, history, keywords):
        matches = 0
        total_keywords = len(keywords)
        
        for message in history:
            content = message.get('content', '').lower()
            for kw in keywords:
                if kw.lower() in content:
                    matches += 1
        
        if matches == 0:
            return 0
        elif matches <= 2:
            return 40
        elif matches <= 4:
            return 70
        else:
            return 100
```

#### 5.1.10 文档版本历史管理

每次 PRD 发生变化都自动保存一个版本，不覆盖。

**文件结构：**

```
docs/
├── human_prd_v1.md          ← 初始版本
├── human_prd_v2.md          ← 用户修改后
├── human_prd_v3.md          ← 再次修改
├── human_prd_current.md     ← 始终指向最新版（复制）
├── machine_prd_v1.yaml
├── machine_prd_v2.yaml
└── machine_prd_current.yaml
```

**版本历史界面功能：**

| 操作 | 说明 |
|---|---|
| 查看历史版本 | 点击版本号查看该版本内容 |
| 对比差异 | 选择两个版本，展示 diff 视图 |
| 回滚版本 | 恢复到某个历史版本（会触发后续 Phase 重置） |

**版本保存时机：**

1. PRD 首次生成
2. 用户修改 PRD 后确认
3. 自动修复导致 PRD 变更
4. 用户手动触发保存

**版本编号规则：**

- 从 v1 开始递增
- 每次保存自动 +1
- 不跳号，不重复

**API 接口定义：**

| 接口 | 方法 | 路径 | 说明 |
|---|---|---|---|
| 获取版本列表 | GET | /api/projects/{name}/versions | 获取项目的所有文档版本 |
| 获取版本内容 | GET | /api/projects/{name}/versions/{version} | 获取指定版本的文档内容 |
| 对比版本 | GET | /api/projects/{name}/versions/diff | 对比两个版本的差异 |
| 回滚版本 | POST | /api/projects/{name}/versions/{version}/rollback | 回滚到指定版本 |

#### 5.1.11 对话上下文持久化机制（三层记忆架构）

LLM 本身没有记忆，平台需要把每一轮对话都存下来，下次恢复时把历史消息重新注入。平台采用三层记忆架构：

**三层记忆策略：**

```
长期记忆（模板数据、PRD、技术文档）→ ChromaDB 语义检索
    +
中期记忆（对话摘要、关键决策点）→ ChromaDB 相似度检索
    +
短期记忆（最近 N 轮对话，默认 N=10）→ SQLite 直接读取
    ↓
三者合并注入下一次 LLM 调用
```

**持久化流程：**

```
每一轮对话
    ↓
立即持久化到 SQLite（短期记忆）
    ↓
存储内容：
    - role（user / assistant / system）
    - content（消息内容）
    - phase（属于哪个 Phase）
    - timestamp
    - token_count（用于控制上下文窗口大小）
```

**长期记忆存储：**

```
项目创建时
    ↓
模板数据（需求描述、技术选型、部署形式）存入 ChromaDB long_term
    ↓
PRD 生成后
    ↓
PRD 内容存入 ChromaDB long_term
```

**中期记忆存储：**

```
摘要触发时机：
1. 每 10 轮对话自动触发一次摘要
2. 累计 token 数超过阈值（默认 8000）时触发
3. 用户手动触发
    ↓
LLM 生成对话摘要
    ↓
摘要内容存入 ChromaDB medium_term
```

**摘要内容结构：**

```
## 对话摘要（Phase {phase}）

### 已确认需求
- 核心功能：{功能描述}
- 用户角色：{角色描述}
- 数据实体：{实体描述}

### 待确认事项
- {待确认项}

### 关键决策
- {决策内容}
```

**恢复时的上下文构建：**

```
恢复项目时
    ↓
读取该项目的所有对话摘要（中期记忆，从 ChromaDB 检索）
    ↓
读取最近 N 轮对话（短期记忆，从 SQLite 读取）
    ↓
检索长期记忆（从 ChromaDB 检索与当前话题相关的模板数据和 PRD）
    ↓
合并为完整上下文
    ↓
注入 LLM 调用
```

**降级策略：**

当 RAG 服务不可用时（如向量数据库未初始化），系统自动降级：
- 使用项目的 `onboarding_data` 作为系统提示
- 仅使用短期记忆和中期记忆（从 SQLite 读取）

**API 接口定义：**

| 接口 | 方法 | 路径 | 说明 |
|---|---|---|---|
| 获取对话历史 | GET | /api/projects/{name}/conversations | 获取项目的对话历史（含摘要） |
| 获取对话摘要 | GET | /api/projects/{name}/conversations/summary | 获取项目的对话摘要 |
| 手动触发摘要 | POST | /api/projects/{name}/conversations/summary | 手动触发对话摘要 |

---

### Phase 2：技术选型

#### 5.2.1 功能描述

LLM 根据 Machine PRD 的内容，自动推荐 1-3 套技术方案，每套方案附说明和适用场景。用户做选择题。平台 Skill 验证选择的合理性，发现冲突时给出警告。

#### 5.2.2 流程

```
读取 machine_prd.yaml
    ↓
Skill 分析关键维度（规模/团队/性能/时间压力）
    ↓
LLM 生成 1-3 套技术方案（含后端/前端/数据层/部署）
    ↓
用户选择方案
    ↓
Skill 验证合理性（如：Rust + 快速原型 → 警告）
    ↓
用户确认
    ↓
更新 project.json（tech_stack 字段）
```

#### 5.2.3 技术栈选项库

**后端：**
- Rust：actix-web + sea-orm（高性能，适合系统级服务）
- Java/Spring Boot：Spring Web + JPA + Spring Cloud（企业级，生态丰富）
- Java/Quarkus：Quarkus + Panache（云原生，启动快）
- Go：Gin/Echo + GORM/ent + gRPC（简洁高效，适合微服务）
- Python：FastAPI + SQLAlchemy（快速开发，AI 集成友好）

**前端：** TypeScript + React + Vite（统一，不提供选项）

**UI 组件库：**
- shadcn/ui（现代，定制灵活）
- Ant Design（企业级，组件丰富）

**数据层：**
- 关系型：PostgreSQL（默认推荐）/ MySQL
- 缓存：Redis（按需）
- 搜索：Elasticsearch（按需）

**部署：**
- K8s 路线：Helm Chart / Go Operator（适合 Rust / Go / Quarkus）
- Spring Cloud 路线：Eureka / Nacos + 部署脚本（适合 Spring Boot）

**CI/CD：**
- GitHub Actions（云原生，推荐）
- Jenkins（自托管，传统）

#### 5.2.4 Skill：`skill_tech_recommend`

**输入：** `machine_prd.yaml`  
**输出：** `tech_options.yaml`（含 1-3 套方案，每套含推荐理由和权衡说明）

#### 5.2.5 Skill：`skill_tech_validate`

**输入：** 用户选择 + `machine_prd.yaml`  
**输出：** 验证报告（通过 / 警告 + 说明）

---

### Phase 3：页面原型设计

#### 5.3.1 功能描述

基于 Machine PRD 中的页面清单，引导用户选择布局风格、配色方案、组件规范，然后生成 HTML + Tailwind CSS 静态原型，同时生成机器可读的页面结构描述 JSON，供后续代码生成消费。

#### 5.3.2 原型格式选择：HTML + Tailwind CSS

选择理由：
- 可直接在浏览器预览，用户体验直观
- LLM 可高质量生成和修改
- 可直接转换为 React 组件
- 无需额外工具（非 Figma、非 Sketch）
- 生成的 `pages_spec.json` 可被脚手架 Skill 直接消费

#### 5.3.3 流程

```
读取 machine_prd.yaml 中的页面清单
    ↓
用户选择布局风格（Dashboard / Landing / Master-Detail / Form-heavy）
    ↓
用户选择配色方案（5套预设 + 自定义）
    ↓
用户选择组件规范（shadcn / Ant Design 风格）
    ↓
Skill 生成每个页面的 HTML + Tailwind 原型
    ↓
用户在浏览器预览并确认
    ↓
Skill 生成 pages_spec.json（机器可读页面结构）
    ↓
更新 project.json
```

#### 5.3.4 布局模板库

| 模板 | 适用场景 | 结构描述 |
|---|---|---|
| Dashboard | 管理后台 | 侧边导航 + 顶部栏 + 内容区 |
| Landing Page | 产品官网 | Hero + Features + CTA + Footer |
| Master-Detail | 列表+详情 | 左侧列表 + 右侧详情面板 |
| Form-heavy | 数据录入 | 分步骤表单 + 验证提示 |
| Card Grid | 内容展示 | 响应式卡片网格 |

#### 5.3.5 配色方案预设（5套）

| 方案名 | 主色 | 风格 |
|---|---|---|
| Corporate Blue | #1E40AF | 专业企业感 |
| Forest Green | #065F46 | 自然清新 |
| Midnight Dark | #0F172A | 深色现代 |
| Warm Sunrise | #92400E | 温暖活力 |
| Pure Minimal | #18181B | 极简黑白 |

#### 5.3.6 Skill：`skill_prototype_generate`

**输入：** `machine_prd.yaml` + 用户布局/配色/组件选择  
**输出：**
- `prototypes/[page_name].html`：每个页面的静态原型
- `pages_spec.json`：页面结构描述（页面名 / 区块 / 组件 / 数据字段绑定）

#### 5.3.7 `pages_spec.json` 结构示例

```json
{
  "pages": [
    {
      "name": "UserList",
      "route": "/users",
      "layout": "Dashboard",
      "sections": [
        {
          "type": "DataTable",
          "entity": "User",
          "fields": ["username", "email", "status", "createdAt"],
          "actions": ["edit", "disable"],
          "pagination": true
        },
        {
          "type": "SearchBar",
          "searchFields": ["username", "email"]
        }
      ]
    }
  ]
}
```

---

### Phase 4：工程脚手架与代码生成

#### 5.4.1 功能描述

分两步执行：第一步生成工程骨架（目录结构 + 接口契约），第二步逐模块生成实现代码（TDD 顺序：先测试后实现）。

#### 5.4.2 工程目录结构

```
{project-name}/
├── backend/
│   ├── common/                  # 公共模块：异常处理、工具类、基础配置
│   ├── service-{name}/          # 每个微服务
│   │   ├── src/
│   │   │   ├── dao/             # 数据访问层
│   │   │   ├── service/         # 业务逻辑层
│   │   │   └── controller/      # 接口层（REST）
│   │   ├── tests/               # 测试代码
│   │   └── Dockerfile
│   └── api-gateway/             # API 网关
├── frontend/
│   ├── src/
│   │   ├── pages/               # 页面组件
│   │   ├── components/          # 公共组件
│   │   ├── hooks/               # 自定义 Hook
│   │   ├── store/               # 状态管理
│   │   └── api/                 # API 调用层
│   └── e2e/                     # Playwright E2E 测试
├── deploy/
│   ├── helm/                    # Helm Charts（K8s 路线）
│   ├── operator/                # Go Operator（K8s 路线）
│   ├── spring-cloud/            # Spring Cloud 配置
│   └── ci/
│       ├── github-actions/      # GitHub Actions workflows
│       └── jenkins/             # Jenkinsfile
├── docs/
│   ├── human_prd.md
│   ├── machine_prd.yaml
│   ├── tech_options.yaml
│   └── pages_spec.json
└── project.json                 # 平台状态文件
```

#### 5.4.3 步骤一：骨架生成

**Skill：`skill_scaffold_generate`**

**输入：** `machine_prd.yaml` + `project.json`（tech_stack）  
**输出：**
- 完整目录结构（含空文件占位）
- `openapi.yaml`（API 接口完整定义）
- 数据库 Schema（SQL 建表语句）
- 每个模块的函数签名文件（无实现，只有接口定义）

**执行完后必须人工确认骨架合理性，再进入步骤二。**

#### 5.4.4 步骤二：逐模块代码生成

**Skill：`skill_code_generate`**

**执行顺序（TDD）：**
```
选择当前模块（如 service-user）
    ↓
生成该模块的单元测试代码
    ↓
生成该模块的集成测试代码
    ↓
生成该模块的实现代码（dao / service / controller）
    ↓
生成该模块的 Dockerfile
    ↓
更新 project.json（completed_modules 字段）
    ↓
选择下一个模块
```

**输入：** 单个模块定义（从 `machine_prd.yaml` 中提取）+ 函数签名文件 + `openapi.yaml`  
**输出：** 该模块完整代码

---

### Phase 5：测试生成与自动修复

#### 5.5.1 测试分层

| 层级 | 工具 | 覆盖范围 | 生成时机 |
|---|---|---|---|
| Unit Test | 各技术栈原生（pytest / JUnit / Go test） | 单个函数/方法 | 实现代码生成前 |
| Integration Test | Testcontainers + 真实数据库 | 模块间调用、数据库操作 | 实现代码生成前 |
| Contract Test | Pact | 微服务接口契约 | 骨架生成后 |
| E2E / UI Test | Playwright | 完整用户流程 | 前端代码生成后 |

#### 5.5.2 自动修复反馈循环

```
运行测试套件
    ↓
[全部通过] → 进入下一阶段
[有失败] → 收集错误信息（stderr + stack trace）
    ↓
将错误信息 + 相关代码 → 喂给 LLM
    ↓
LLM 生成修复代码
    ↓
应用修复
    ↓
重新运行测试
    ↓
[重试次数 < 最大值（默认3次）] → 继续循环
[重试次数 ≥ 最大值] → 暂停，通知用户人工介入
```

#### 5.5.3 Skill：`skill_test_unit_generate`

**输入：** 模块函数签名 + 实体定义  
**输出：** 单元测试文件

#### 5.5.4 Skill：`skill_test_integration_generate`

**输入：** `openapi.yaml` + 数据库 Schema  
**输出：** 集成测试文件（含 Testcontainers 配置）

#### 5.5.5 Skill：`skill_test_e2e_generate`

**输入：** `pages_spec.json` + `openapi.yaml`  
**输出：** Playwright 测试文件（按用户流程组织）

#### 5.5.6 Skill：`skill_autofix`

**输入：** 测试错误日志 + 相关源代码文件  
**输出：** 修复后的代码文件  
**约束：** 最多执行 3 次；每次修改范围只限于报错相关文件

---

### Phase 6：部署配置生成

#### 5.6.1 功能描述

根据用户在 Phase 2 选择的技术栈和部署路线，生成对应的部署配置文件和 CI/CD 流水线配置。平台只生成配置文件，不执行实际部署。

#### 5.6.2 K8s 路线（适用于 Rust / Go / Quarkus）

**Skill：`skill_deploy_k8s_helm`**

**输出：**
```
deploy/helm/
├── Chart.yaml
├── values.yaml
├── values-prod.yaml
└── templates/
    ├── deployment.yaml
    ├── service.yaml
    ├── ingress.yaml
    ├── configmap.yaml
    └── hpa.yaml
```

**Skill：`skill_deploy_k8s_operator`**

适用场景：有状态服务、需要自定义控制逻辑  
**输出：** Go Operator 项目（含 CRD 定义 + Controller 代码框架）

#### 5.6.3 Spring Cloud 路线（适用于 Spring Boot）

**Skill：`skill_deploy_spring_cloud`**

**输出：**
```
deploy/spring-cloud/
├── docker-compose.yml           # 本地开发环境
├── application-config/          # Spring Cloud Config 配置
├── eureka-server/               # 服务注册中心配置
└── scripts/
    ├── deploy.sh                # 部署脚本
    └── rollback.sh              # 回滚脚本
```

#### 5.6.4 CI/CD 路线

**Skill：`skill_cicd_github_actions`**

**输出：**
```
deploy/ci/github-actions/
├── build.yml                    # 构建并推送镜像
├── test.yml                     # 运行测试套件
└── deploy.yml                   # 触发部署
```

**Skill：`skill_cicd_jenkins`**

**输出：**
```
deploy/ci/jenkins/
└── Jenkinsfile                  # 含完整流水线定义
```

#### 5.6.5 部署前检查 Skill：`skill_deploy_preflight`

在生成任何部署配置之前运行，检查：
- 环境变量是否完整定义
- 镜像 Tag 是否明确（非 `latest`）
- 数据库连接字符串是否已参数化
- Secrets 是否通过 K8s Secret / 环境变量注入（不可硬编码）

---

## 6. Skill 系统设计

### 6.1 Skill 是什么

Skill 是平台的最小执行单元，是一段有明确输入/输出约定的代码或 Prompt 模板。每个 Skill：
- 从 `project.json` 读取当前状态
- 执行固定逻辑（代码）或调用 LLM（Prompt）
- 将产出写入文件系统
- 更新 `project.json`

### 6.2 Skill 目录结构

```
skills/
├── prd/
│   └── skill_prd_generate/
│       ├── SKILL.md            # Skill 说明文档（给 LLM 读的）
│       ├── prompt.yaml         # LLM Prompt 模板
│       ├── schema.yaml         # 输入/输出 Schema
│       └── runner.py           # 执行脚本
├── tech/
│   ├── skill_tech_recommend/
│   └── skill_tech_validate/
├── prototype/
│   └── skill_prototype_generate/
├── scaffold/
│   ├── skill_scaffold_generate/
│   └── skill_code_generate/
├── test/
│   ├── skill_test_unit_generate/
│   ├── skill_test_integration_generate/
│   ├── skill_test_e2e_generate/
│   └── skill_autofix/
└── deploy/
    ├── skill_deploy_k8s_helm/
    ├── skill_deploy_k8s_operator/
    ├── skill_deploy_spring_cloud/
    ├── skill_cicd_github_actions/
    ├── skill_cicd_jenkins/
    └── skill_deploy_preflight/
```

### 6.3 SKILL.md 统一格式

每个 Skill 的 `SKILL.md` 必须包含以下字段，供 LLM 读取执行：

```markdown
# Skill: {skill_name}

## 触发条件
[何时调用此 Skill]

## 前置依赖
[必须已完成的 Phase 或文件]

## 输入
[输入文件路径和格式说明]

## 执行步骤
[step-by-step 执行说明]

## 输出
[输出文件路径和格式说明]

## 更新 project.json
[哪些字段需要更新]

## 错误处理
[遇到错误时的行为]

## 示例
[输入/输出示例]
```

### 6.4 Prompt 模板规范

每个 Skill 的 `prompt.yaml` 包含以下结构，供 LLM 调用时使用：

```yaml
skill: "{skill_name}"
version: "1.0"

system_prompt: |
  你是一个专业的 {skill_category} 工程师。
  你必须严格按照以下规则执行：
  1. 只输出指定格式的结果
  2. 如果输入信息不足，返回 ERROR 状态并说明缺少的信息
  3. 输出必须符合项目的技术栈和代码风格

user_prompt: |
  请根据以下输入，执行 {skill_name}：
  
  输入：
  {input_variables}
  
  要求：
  1. {requirement_1}
  2. {requirement_2}
  3. {requirement_3}
  
  输出格式：
  {output_format}

output_schema:
  type: object
  properties:
    status:
      type: string
      enum: ["SUCCESS", "ERROR", "NEED_MORE_INFO"]
    message:
      type: string
    artifacts:
      type: array
      items:
        type: object
        properties:
          file_path:
            type: string
          content:
            type: string
```

### 6.5 核心 Skill Prompt 模板详解

#### 6.5.1 skill_prd_generate

```yaml
skill: "skill_prd_generate"
version: "1.0"

system_prompt: |
  你是一个资深产品经理和技术架构师。
  你负责将用户的对话历史转化为两份高质量的 PRD 文档。
  必须严格遵循以下规则：
  1. Human PRD 必须清晰、结构化、易于阅读
  2. Machine PRD 必须严格符合 Section 11 的 Schema
  3. 如果信息不足，返回 NEED_MORE_INFO 并列出缺少的维度

user_prompt: |
  请根据以下对话历史，生成 Human PRD 和 Machine PRD：
  
  对话历史：
  {conversation_history}
  
  需求完整度评分：{completeness_score}/100
  
  要求：
  1. Human PRD 包含：产品概述、功能模块、数据模型、API 接口清单、非功能需求、外部集成
  2. Machine PRD 严格按照 Section 11 的 Schema 格式输出
  3. 确保所有实体关系清晰，API 定义完整
  4. 代码命名使用 PascalCase（类名）和 camelCase（方法/字段名）
  
  输出格式：
  ```json
  {
    "status": "SUCCESS",
    "message": "PRD 生成完成",
    "artifacts": [
      {
        "file_path": "docs/human_prd.md",
        "content": "{human_prd_markdown}"
      },
      {
        "file_path": "docs/machine_prd.yaml",
        "content": "{machine_prd_yaml}"
      }
    ]
  }
  ```

output_schema:
  type: object
  properties:
    status:
      type: string
      enum: ["SUCCESS", "ERROR", "NEED_MORE_INFO"]
    message:
      type: string
    artifacts:
      type: array
      items:
        type: object
        properties:
          file_path:
            type: string
          content:
            type: string
```

#### 6.5.2 skill_tech_recommend

```yaml
skill: "skill_tech_recommend"
version: "1.0"

system_prompt: |
  你是一个资深技术架构师，擅长为不同类型的项目推荐合适的技术栈。
  必须严格遵循以下规则：
  1. 推荐必须基于项目需求，不能盲目推荐热门技术
  2. 每套方案必须包含权衡分析
  3. 如果无法确定，返回 ERROR 并说明原因

user_prompt: |
  请根据以下 Machine PRD，推荐 1-3 套技术方案：
  
  Machine PRD：
  {machine_prd_content}
  
  要求：
  1. 每套方案包含：后端框架、前端框架、数据库、缓存、部署方式、CI/CD
  2. 每套方案附带：推荐理由、适用场景、潜在风险
  3. 优先考虑项目的规模、预期用户量、团队背景
  
  输出格式：
  ```yaml
  tech_options:
    - name: "{方案名称}"
      backend: "{后端技术}"
      backend_framework: "{框架}"
      orm: "{ORM工具}"
      frontend: "react"
      ui_library: "{UI组件库}"
      database: "{数据库}"
      cache: "{缓存}"
      deployment: "{部署方式}"
      cicd: "{CI/CD工具}"
      reason: "{推荐理由}"
      tradeoffs: "{权衡分析}"
      risk: "{潜在风险}"
  ```

output_schema:
  type: object
  properties:
    status:
      type: string
      enum: ["SUCCESS", "ERROR"]
    message:
      type: string
    artifacts:
      type: array
      items:
        type: object
        properties:
          file_path:
            type: string
          content:
            type: string
```

#### 6.5.3 skill_prototype_generate

```yaml
skill: "skill_prototype_generate"
version: "1.0"

system_prompt: |
  你是一个前端工程师和 UI 设计师。
  你负责将页面结构描述转化为高质量的 HTML + Tailwind CSS 原型。
  必须严格遵循以下规则：
  1. HTML 必须语义化，结构清晰
  2. CSS 必须使用 Tailwind，不使用自定义 CSS
  3. 原型必须响应式，支持桌面和移动端

user_prompt: |
  请根据以下输入，生成页面原型：
  
  Machine PRD：
  {machine_prd_content}
  
  用户选择：
  - 布局风格：{layout_style}
  - 配色方案：{color_scheme}
  - 组件规范：{component_spec}
  
  要求：
  1. 每个页面生成独立的 HTML 文件
  2. 使用 Tailwind CSS v3，通过 CDN 引入
  3. 页面结构必须与 pages_spec.json 一致
  4. 包含占位数据，便于预览
  
  输出格式：
  ```json
  {
    "status": "SUCCESS",
    "message": "原型生成完成",
    "artifacts": [
      {
        "file_path": "prototypes/{page_name}.html",
        "content": "{html_content}"
      },
      ...
    ]
  }
  ```

output_schema:
  type: object
  properties:
    status:
      type: string
      enum: ["SUCCESS", "ERROR"]
    message:
      type: string
    artifacts:
      type: array
      items:
        type: object
        properties:
          file_path:
            type: string
          content:
            type: string
```

#### 6.5.4 skill_scaffold_generate

```yaml
skill: "skill_scaffold_generate"
version: "1.0"

system_prompt: |
  你是一个资深后端架构师。
  你负责根据技术栈生成完整的工程骨架。
  必须严格遵循以下规则：
  1. 目录结构必须符合 Section 5.4.2 的规范
  2. API 定义必须符合 OpenAPI 3.0 标准
  3. 数据库 Schema 必须与实体定义一致

user_prompt: |
  请根据以下输入，生成工程骨架：
  
  Machine PRD：
  {machine_prd_content}
  
  技术栈：
  {tech_stack}
  
  要求：
  1. 生成完整目录结构（含空文件占位）
  2. 生成 openapi.yaml（完整 API 定义）
  3. 生成数据库 Schema（SQL 建表语句）
  4. 生成每个模块的函数签名文件
  5. 包含基础配置文件（.gitignore, README.md 等）
  
  输出格式：
  ```json
  {
    "status": "SUCCESS",
    "message": "骨架生成完成",
    "artifacts": [
      {
        "file_path": "{file_path}",
        "content": "{file_content}"
      },
      ...
    ]
  }
  ```

output_schema:
  type: object
  properties:
    status:
      type: string
      enum: ["SUCCESS", "ERROR"]
    message:
      type: string
    artifacts:
      type: array
      items:
        type: object
        properties:
          file_path:
            type: string
          content:
            type: string
```

#### 6.5.5 skill_code_generate

```yaml
skill: "skill_code_generate"
version: "1.0"

system_prompt: |
  你是一个资深全栈工程师。
  你负责按照 TDD 方式逐模块生成代码。
  必须严格遵循以下规则：
  1. 先写测试，后写实现
  2. 代码必须符合技术栈的最佳实践
  3. 代码风格必须一致
  4. 必须包含完整的错误处理

user_prompt: |
  请根据以下输入，生成 {module_name} 模块的完整代码：
  
  模块定义：
  {module_definition}
  
  技术栈：
  {tech_stack}
  
  OpenAPI 定义：
  {openapi_definition}
  
  函数签名：
  {function_signatures}
  
  要求（TDD 顺序）：
  1. 生成单元测试代码
  2. 生成集成测试代码
  3. 生成实现代码（dao / service / controller）
  4. 生成 Dockerfile
  5. 代码必须通过测试
  6. 包含完整的注释
  
  输出格式：
  ```json
  {
    "status": "SUCCESS",
    "message": "模块 {module_name} 代码生成完成",
    "artifacts": [
      {
        "file_path": "{file_path}",
        "content": "{file_content}"
      },
      ...
    ]
  }
  ```

output_schema:
  type: object
  properties:
    status:
      type: string
      enum: ["SUCCESS", "ERROR"]
    message:
      type: string
    artifacts:
      type: array
      items:
        type: object
        properties:
          file_path:
            type: string
          content:
            type: string
```

#### 6.5.6 skill_autofix

```yaml
skill: "skill_autofix"
version: "1.0"

system_prompt: |
  你是一个资深调试工程师。
  你负责根据测试错误日志修复代码。
  必须严格遵循以下规则：
  1. 只修改与错误相关的代码
  2. 修复必须最小化，不引入新问题
  3. 如果无法修复，返回 ERROR

user_prompt: |
  请根据以下测试错误日志，修复代码：
  
  错误日志：
  {error_log}
  
  相关源代码：
  {source_code}
  
  重试次数：{retry_count}/{max_retries}
  
  要求：
  1. 分析错误原因
  2. 生成修复后的代码
  3. 修复范围仅限于报错文件
  4. 保持代码风格一致
  
  输出格式：
  ```json
  {
    "status": "SUCCESS",
    "message": "代码修复完成",
    "artifacts": [
      {
        "file_path": "{file_path}",
        "content": "{fixed_content}"
      },
      ...
    ]
  }
  ```

output_schema:
  type: object
  properties:
    status:
      type: string
      enum: ["SUCCESS", "ERROR"]
    message:
      type: string
    artifacts:
      type: array
      items:
        type: object
        properties:
          file_path:
            type: string
          content:
            type: string
```

---

## 7. 状态管理机制

### 7.1 project.json 结构

```json
{
  "project_id": "uuid",
  "project_name": "my-todo-app",
  "created_at": "2026-06-28T10:00:00Z",
  "current_phase": "scaffold",

  "phases": {
    "prd":       { "status": "completed", "completed_at": "..." },
    "tech":      { "status": "completed", "completed_at": "..." },
    "prototype": { "status": "completed", "completed_at": "..." },
    "scaffold":  { "status": "in_progress", "started_at": "..." },
    "test":      { "status": "pending" },
    "deploy":    { "status": "pending" }
  },

  "tech_stack": {
    "backend": "go",
    "backend_framework": "gin",
    "orm": "gorm",
    "frontend": "react",
    "ui_library": "shadcn",
    "database": "postgresql",
    "cache": "redis",
    "deployment": "k8s_helm",
    "cicd": "github_actions"
  },

  "modules": {
    "service-user":  { "status": "completed" },
    "service-order": { "status": "in_progress", "tests_passing": false, "retry_count": 1 },
    "service-payment": { "status": "pending" }
  },

  "artifacts": {
    "human_prd":    "docs/human_prd.md",
    "machine_prd":  "docs/machine_prd.yaml",
    "pages_spec":   "docs/pages_spec.json",
    "openapi_spec": "docs/openapi.yaml",
    "db_schema":    "docs/schema.sql"
  },

  "settings": {
    "max_autofix_retries": 3,
    "llm_provider": "anthropic",
    "llm_model": "claude-sonnet-4-6"
  }
}
```

**settings 字段说明：**

`project.json` 中的 `settings` 字段存储项目级别的配置，其中 `llm_provider` 和 `llm_model` 记录该项目上次使用的 LLM 配置。实际运行时，LLM 配置的优先级如下：

1. **环境变量**（最高优先级）：`LLM_PROVIDER`、`LLM_MODEL`、`LLM_API_KEY`
2. **全局 LLM 设置**（`llm_settings` 表）：通过设置页面配置
3. **项目级别设置**（`project.json`）：记录项目上次使用的配置，可作为默认值
4. **默认值**（最低优先级）：Anthropic + claude-sonnet-4-6

### 7.2 状态流转规则

- 每个 Phase 只能在前一 Phase `completed` 后才能启动
- `in_progress` 状态的 Phase 可以暂停和恢复
- 用户可以回退到任意已完成的 Phase 重新执行（会清除后续 Phase 的状态）

---

## 8. 非功能需求

### 8.1 性能

- LLM 调用响应：流式输出，首 token 延迟 < 2s
- 单模块代码生成：< 60s
- 原型页面生成：< 30s 每页

### 8.2 可用性

- Web 界面支持暂停 / 恢复任意阶段
- 生成过程中断后可从断点继续（基于 `project.json` 状态）
- 所有生成产物持久化到本地文件系统

### 8.3 可扩展性

- LLM 提供商通过适配层接入，支持随时切换（OpenAI / Anthropic / Gemini / Ollama）
- 新技术栈通过新增 Skill 支持，不改动核心逻辑
- Skill 可独立版本化和更新

### 8.4 安全性

- LLM API Key 优先通过环境变量注入；如通过设置页面输入，需加密存储到数据库
- API Key 在 API 响应中不返回（脱敏处理）
- 生成的代码不自动执行，只写入文件
- 本地测试执行在沙箱环境中运行

---

## 9. 技术栈约束

### 9.1 平台本身的技术栈（DevSmart 自身）

| 层级 | 技术选择 | 原因 |
|---|---|---|
| 后端 | Python + FastAPI | LLM 生态最丰富，开发效率高 |
| 数据库 | SQLite + SQLAlchemy | 零部署、开箱即用、适合轻量级应用 |
| 向量数据库 | ChromaDB | 嵌入式、轻量级、支持语义检索 |
| 前端 | TypeScript + React + Vite | 统一前端技术栈 |
| UI | Tailwind CSS 4.3+ | 现代、定制灵活、无需配置文件 |
| LLM 适配 | LiteLLM（统一多 LLM 接口） | 一套代码接所有 LLM |
| 测试执行 | subprocess + Docker | 隔离环境运行生成的测试 |

### 9.2 生成目标技术栈（DevSmart 能生成的）

见 Phase 2 Section 5.2.3 技术栈选项库。

### 9.3 数据库迁移说明

**当前版本：** 使用 SQLite 作为默认数据库，无需额外部署。

**未来版本：** 支持 PostgreSQL 作为可选数据库，通过环境变量配置切换：

```bash
# SQLite（默认）
DATABASE_URL=sqlite:///./devsmart.db

# PostgreSQL（可选）
DATABASE_URL=postgresql://user:password@localhost/devsmart
```

---

## 10. 里程碑计划

| 里程碑 | 包含功能 | 目标 | 状态 |
|---|---|---|---|
| M1: 项目管理 | Phase 0 完整流程（项目创建/列表/恢复 + 模板向导） | 能创建项目并填写初始需求 | ✅ 已完成 |
| M2: 核心对话与 PRD | Phase 1 完整流程（对话 + PRD 生成 + 下载） | 能生成并下载双版本 PRD，可交付给 Code Agent | ✅ 已完成 |
| M3: 技术选型 | Phase 2 完整流程（推荐 + 验证） | 能生成技术方案文档 | ⏳ 待开发 |
| M4: 原型生成 | Phase 3 完整流程 | 能生成可预览的 HTML 原型 | ⏳ 待开发 |
| M5: 脚手架 | Phase 4 步骤一（骨架生成） | 能生成完整工程目录和接口定义 | ⏳ 待开发 |
| M6: 代码生成 | Phase 4 步骤二（逐模块生成） | 能生成可运行代码（Go 技术栈优先） | ⏳ 待开发 |
| M7: 测试闭环 | Phase 5 完整流程（生成 + 自动修复） | 测试通过率 > 80% | ⏳ 待开发 |
| M8: 部署配置 | Phase 6 完整流程 | 能生成可用的 Helm Chart 和 CI/CD | ⏳ 待开发 |

### 当前版本特性

**已实现：**
- 项目管理（创建、列表、恢复）
- 模板向导（需求描述、技术选型、部署形式）
- 需求澄清对话流程
- 双版本 PRD 生成（Human PRD + Machine PRD）
- PRD 下载功能
- RAG 三层记忆架构（长期/中期/短期）
- ChromaDB 向量数据库集成
- 对话摘要生成与存储

**核心价值：**
- 用户通过模板向导和对话澄清需求
- 平台生成结构化 PRD 文档
- 用户下载 PRD 后可交给任何 Code Agent 进行代码生成

---

## 11. 附录：Machine-readable PRD Schema

以下为 `machine_prd.yaml` 的完整 Schema 定义。所有 Skill 以此为标准消费 PRD。

```yaml
# machine_prd.yaml Schema v1.0

project:
  name: string                    # 项目名称（英文，用于目录和包名）
  display_name: string            # 展示名称（中英文均可）
  description: string             # 一句话描述
  version: "1.0"

users:
  - role: string                  # 角色名（如 admin / user / guest）
    description: string
    permissions: [string]         # 权限列表

modules:
  - name: string                  # 模块名（英文，对应 service-{name}）
    description: string
    entities:
      - name: string              # 实体名（PascalCase）
        fields:
          - name: string
            type: string          # string / int / float / bool / datetime / enum / uuid
            required: boolean
            unique: boolean
            values: [string]      # 仅 enum 类型使用
        relations:
          - type: string          # one-to-many / many-to-many / one-to-one
            target: string        # 目标实体名
    apis:
      - method: string            # GET / POST / PUT / DELETE / PATCH
        path: string              # 如 /users/:id
        description: string
        auth_required: boolean
        roles: [string]           # 允许访问的角色
        request_body: object      # 可选，请求体字段描述
        response: object          # 响应体字段描述

pages:
  - name: string                  # 页面名（PascalCase）
    route: string                 # URL 路径
    description: string
    auth_required: boolean
    roles: [string]
    data_sources: [string]        # 依赖的 API 路径列表

non_functional:
  expected_users: int             # 预期用户量
  concurrent_requests: int        # 预期并发数
  auth_type: string               # jwt / session / oauth2
  data_sensitivity: string        # low / medium / high
  availability: string            # 99% / 99.9% / 99.99%

integrations:
  - name: string                  # 第三方服务名
    type: string                  # payment / email / sms / storage / auth
    required: boolean
```

---

## 12. LLM 执行指南（Execution Guide）

### 12.1 概述

本文档是一份 **可执行的技术规格说明书**。任何 LLM 阅读本文档后，应能独立实现 DevSmart 平台的完整工程。

**核心原则：**
- 按 Phase 顺序逐步实现
- 每个 Phase 的 Skill 必须独立可测试
- 代码必须通过所有测试才能进入下一 Phase
- 严格遵循 Section 6 的 Skill 模板规范

### 12.2 执行流程

```
读取本文档（DevSmart_PRD_v1.0.md）
    ↓
理解平台架构和技术栈约束（Section 3, 9）
    ↓
从 Phase 0 开始实现（项目管理是入口）
    ↓
每个 Phase 实现流程：
    ├── 实现该 Phase 的所有 Skill（SKILL.md + prompt.yaml + runner.py）
    ├── 编写单元测试
    ├── 运行测试验证
    ├── 更新 project.json 状态
    └── 进入下一 Phase
    ↓
所有 Phase 完成后，进行集成测试
    ↓
生成部署配置
```

### 12.3 Phase 0 实现指导

**目标：** 实现项目管理入口，支持创建/查找/恢复项目

**Step 1：创建项目结构**

```
devsmart/
├── backend/
│   ├── main.py                    # FastAPI 入口
│   ├── requirements.txt           # 依赖列表
│   ├── config/                    # 配置文件
│   │   └── settings.py
│   ├── services/                  # 核心服务
│   │   ├── project_service.py     # 项目管理服务
│   │   ├── conversation_service.py
│   │   ├── prd_service.py
│   │   ├── completeness_service.py
│   │   └── summary_service.py     # 对话摘要服务
│   ├── skills/                    # Skill 目录
│   │   └── prd/
│   │       └── skill_prd_generate/
│   │           ├── SKILL.md
│   │           ├── prompt.yaml
│   │           ├── schema.yaml
│   │           └── runner.py
│   ├── models/                    # 数据模型
│   │   ├── project.py
│   │   ├── conversation.py
│   │   ├── conversation_summary.py
│   │   ├── document_version.py
│   │   └── prd.py
│   ├── routers/                   # API 路由
│   │   ├── project.py
│   │   ├── conversation.py
│   │   ├── prd.py
│   │   ├── version.py
│   │   └── settings.py             # LLM 设置路由
│   └── utils/                     # 工具类
│       ├── llm_client.py          # LLM 适配层
│       └── yaml_parser.py
├── frontend/
│   ├── package.json
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── components/
│   │   │   ├── ProjectList.tsx
│   │   │   ├── ProjectForm.tsx
│   │   │   ├── ChatInterface.tsx
│   │   │   ├── PRDPreview.tsx
│   │   │   ├── CompletenessBar.tsx
│   │   │   ├── VersionHistory.tsx
│   │   │   └── LLMSettings.tsx     # LLM 设置页面
│   │   ├── pages/
│   │   │   └── HomePage.tsx
│   │   ├── services/
│   │   │   └── api.ts
│   │   └── types/
│   │       └── index.ts
│   └── index.html
└── projects/                      # 项目存储目录
    └── {project_name}/
        ├── project.json
        └── docs/
```

**Step 2：实现 LLM 适配层**

`backend/utils/llm_client.py` 必须支持：
- LiteLLM 统一接口
- 流式输出
- 支持 OpenAI / Anthropic / Gemini / Ollama

```python
from litellm import completion
import os

class LLMClient:
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "anthropic")
        self.model = os.getenv("LLM_MODEL", "claude-sonnet-4-6")
    
    def chat(self, messages, stream=False):
        return completion(
            model=f"{self.provider}/{self.model}",
            messages=messages,
            stream=stream,
            temperature=0.7
        )
    
    def generate_prd(self, conversation_history):
        prompt = self._build_prd_prompt(conversation_history)
        return self.chat([{"role": "user", "content": prompt}])
```

**Step 3：实现需求完整度评估服务**

`backend/services/completeness_service.py` 必须实现 Section 5.1.3 的评分算法：

```python
class CompletenessService:
    def calculate(self, conversation_history):
        scores = {
            "core_features": self._evaluate_core_features(conversation_history),
            "user_roles": self._evaluate_user_roles(conversation_history),
            "data_entities": self._evaluate_data_entities(conversation_history),
            "non_functional": self._evaluate_non_functional(conversation_history),
            "integrations": self._evaluate_integrations(conversation_history)
        }
        
        weights = {"core_features": 0.3, "user_roles": 0.15, "data_entities": 0.25, "non_functional": 0.15, "integrations": 0.15}
        
        total = sum(scores[key] * weights[key] for key in scores)
        return round(total, 2)
    
    def _evaluate_core_features(self, history):
        # 检查是否提到了功能模块、用户故事等
        keywords = ["功能", "模块", "feature", "user story", "用户故事"]
        if any(kw in message['content'] for message in history for kw in keywords):
            return 80
        return 20
```

**Step 4：实现对话服务**

`backend/services/conversation_service.py` 必须实现：
- 多轮对话管理
- LLM 追问逻辑
- 完整度评估触发

**Step 5：实现 PRD 生成 Skill**

`backend/skills/prd/skill_prd_generate/runner.py` 必须实现：
- 读取对话历史
- 调用 LLM 生成双版本 PRD
- 写入文件系统
- 更新 project.json

**Step 6：实现前端对话界面**

前端必须包含：
- 聊天输入框
- 对话历史展示
- 需求完整度进度条
- PRD 预览面板
- 用户确认按钮

### 12.4 验证标准

每个 Phase 实现完成后，必须满足以下验证标准：

**Phase 0 验证标准：**
- [ ] 用户可以创建新项目（输入项目名称）
- [ ] 项目名称唯一校验
- [ ] 项目列表展示（项目名称、当前阶段、最后修改时间、PRD 版本）
- [ ] 项目列表支持搜索
- [ ] 选择已有项目能恢复到上次中断位置
- [ ] 创建项目时自动生成 project.json
- [ ] LLM 设置页面可访问
- [ ] 支持选择 LLM 提供商（OpenAI / Anthropic / Google / Ollama）
- [ ] 支持选择模型（根据提供商动态显示）
- [ ] API Key 输入（密码隐藏）
- [ ] 温度参数设置（滑块 0-1）
- [ ] 测试连接功能正常
- [ ] 设置保存后立即生效

**Phase 1 验证标准：**
- [ ] 用户可以输入初步想法
- [ ] LLM 能自动分析缺失维度并追问
- [ ] 需求完整度能实时计算和展示
- [ ] 完整度 ≥ 80 时能触发 PRD 生成
- [ ] 能生成 human_prd.md 和 machine_prd.yaml
- [ ] PRD 版本历史自动保存
- [ ] 对话历史持久化到数据库
- [ ] 对话摘要自动生成（每 20 轮或 token 超阈值）
- [ ] 恢复项目时能重建完整上下文
- [ ] project.json 状态正确更新

### 12.4.1 Playwright 测试规范

**目的：** 通过自动化 E2E 测试确保平台功能的正确性和稳定性。每次功能开发完成后，自动生成测试用例。

#### 12.4.1.1 测试框架与配置

| 配置项 | 值 |
|---|---|
| 测试框架 | Playwright（Node.js） |
| 测试文件位置 | `frontend/tests/` |
| 配置文件 | `frontend/playwright.config.ts` |
| 浏览器 | Chromium（主要）、Firefox、Safari |
| 运行命令 | `npx playwright test` |

#### 12.4.1.2 测试自动生成机制

**触发时机：**
- 每个 Phase 完成时自动生成对应测试用例
- 每次 API 接口变更后重新生成测试

**生成流程：**
```
Phase 完成
    ↓
Skill: skill_test_generate 自动执行
    ↓
读取 API 文档（OpenAPI Schema）
    ↓
分析接口参数、返回值、约束条件
    ↓
生成 Playwright 测试用例
    ↓
写入 frontend/tests/{模块名}.spec.ts
```

**测试用例自动生成规则：**

| 接口类型 | 自动生成测试 |
|---|---|
| GET 查询接口 | 成功查询 + 404 边界 |
| POST 创建接口 | 成功创建 + 验证失败（参数校验） |
| PUT 更新接口 | 成功更新 + 不存在资源 |
| DELETE 删除接口 | 成功删除 + 不存在资源 |

#### 12.4.1.3 测试隔离规范

```typescript
// 测试隔离：每个测试使用独立数据
test.beforeEach(async ({ request }) => {
  // 生成唯一标识避免测试冲突
  projectName = `test-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  // 创建测试数据
});

test.afterEach(async ({ request }) => {
  // 清理测试数据
  await request.delete(`/api/projects/${projectName}`).catch(() => {});
});
```

#### 12.4.1.4 CI/CD 集成

```yaml
# .github/workflows/test.yml
name: E2E Tests

on:
  push:
    branches: [main, develop]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: cd frontend && npm install
      - run: cd frontend && npx playwright install --with-deps
      - name: Start services
        run: |
          docker-compose up -d
          ./start.sh &
          sleep 10
      - name: Run tests
        run: cd frontend && npx playwright test
```

---

### 12.5 交付物清单

实现完成后，必须产出以下文件：

```
devsmart/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── config/settings.py
│   ├── services/
│   │   ├── project_service.py
│   │   ├── conversation_service.py
│   │   ├── prd_service.py
│   │   ├── completeness_service.py
│   │   └── summary_service.py
│   ├── skills/prd/skill_prd_generate/
│   │   ├── SKILL.md
│   │   ├── prompt.yaml
│   │   ├── schema.yaml
│   │   └── runner.py
│   ├── models/
│   │   ├── project.py
│   │   ├── conversation.py
│   │   ├── conversation_summary.py
│   │   ├── document_version.py
│   │   └── prd.py
│   ├── routers/
│   │   ├── project.py
│   │   ├── conversation.py
│   │   ├── prd.py
│   │   ├── version.py
│   │   └── settings.py
│   └── utils/
│       ├── llm_client.py
│       └── yaml_parser.py
├── frontend/
│   ├── package.json
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── components/
│   │   │   ├── ProjectList.tsx
│   │   │   ├── ProjectForm.tsx
│   │   │   ├── ChatInterface.tsx
│   │   │   ├── PRDPreview.tsx
│   │   │   ├── CompletenessBar.tsx
│   │   │   ├── LLMSettings.tsx
│   │   │   └── VersionHistory.tsx
│   │   ├── pages/
│   │   │   └── HomePage.tsx
│   │   ├── services/
│   │   │   └── api.ts
│   │   └── types/
│   │       └── index.ts
│   └── index.html
├── projects/
│   └── {project_name}/
│       ├── project.json
│       └── docs/
│           ├── human_prd_v1.md
│           ├── human_prd_current.md
│           ├── machine_prd_v1.yaml
│           └── machine_prd_current.yaml
├── frontend/
│   └── tests/
│       ├── projects.spec.ts       # 项目管理 E2E 测试
│       ├── settings.spec.ts       # LLM 设置测试
│       └── conversations.spec.ts   # 对话功能测试
└── database/
    └── schema.sql                 # PostgreSQL 表结构
```

---

*文档结束*

*本文档由 DevSmart 平台对话引导生成，经用户确认后作为工程生成的唯一依据。*  
*任何 LLM 阅读本文档后，应能独立实现 DevSmart 平台的完整工程。*
