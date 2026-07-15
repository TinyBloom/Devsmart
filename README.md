# DevSmart

DevSmart 是一个基于 LLM 驱动的软件开发平台，帮助团队从需求分析到代码生成的全流程自动化。

## 功能特性

- **需求分析** - 智能分析需求缺口，计算完整度评分，自动生成追问问题
- **PRD 生成** - 生成双版本 PRD（Human PRD 面向人类评审，Machine PRD 面向机器解析）
- **技能系统** - 模块化技能架构，支持需求分析、PRD 生成、技术选型等技能
- **工作流引擎** - YAML 定义工作流，按步骤执行多个技能
- **模板系统** - 支持通用 SaaS、电商、移动应用、API 服务等 PRD 模板
- **技术栈推荐** - 基于约束分析生成技术栈建议和 ADR
- **三层记忆架构** - 基于 RAG 的长期/中期/短期记忆，提升对话上下文理解能力
- **模板向导** - 创建项目时填写需求模板，包括需求描述、技术选型、部署形式等

## 技术栈

### 后端
- Python 3.11+
- FastAPI 0.104+
- SQLAlchemy 2.0+
- SQLite (默认) / PostgreSQL (可选)
- LiteLLM (多提供商 LLM 适配)
- Pydantic
- ChromaDB (向量数据库，RAG)

### 前端
- React 18+
- TypeScript
- Vite 6.0+
- React Router DOM
- React Markdown (Markdown 渲染)
- Axios (HTTP 客户端)
- Tailwind CSS 4.3+

## 目录结构

```
devsmart/
├── backend/                    # 后端服务
│   ├── config/                 # 配置文件
│   ├── models/                 # 数据库模型
│   ├── routers/                # API 路由
│   ├── services/               # 业务逻辑服务
│   │   └── rag_service.py      # RAG 向量检索服务
│   ├── skills/                 # 技能系统
│   │   ├── prd/                # PRD 相关技能
│   │   ├── requirement/        # 需求相关技能
│   │   └── tech/               # 技术相关技能
│   ├── templates/              # PRD 模板
│   ├── utils/                  # 工具函数
│   └── workflows/              # 工作流定义
├── frontend/                   # 前端应用
│   └── src/
│       ├── components/         # React 组件
│       │   └── OnboardingWizard.tsx  # 模板填写向导
│       ├── pages/              # 页面组件
│       ├── services/           # API 服务
│       └── types/              # TypeScript 类型定义
├── database/                   # 数据库 schema
├── projects/                   # 项目文件存储
├── docs/                       # 文档
│   └── onboarding_context_design.md  # RAG 三层记忆架构设计文档
└── tests/                      # 测试用例
```

## 环境设置

### 前置依赖

- Python 3.11+
- Node.js 18+

### 1. 克隆项目

```bash
git clone <repository-url>
cd devsmart
```

### 2. 后端设置

#### 创建虚拟环境

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows
```

#### 安装依赖

```bash
pip install -r requirements.txt
```

#### 配置环境变量

创建 `.env` 文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置以下关键项：

```env
# 数据库配置 - 默认使用 SQLite，无需额外安装
DATABASE_URL=sqlite+aiosqlite:///./devsmart.db

# LLM 配置 - 支持 OpenAI、Anthropic、Google 等多种提供商
LLM_PROVIDER=openai
LLM_API_KEY=your-api-key
LLM_MODEL=gpt-4o

# 应用配置
APP_NAME=DevSmart
APP_VERSION=1.0.0
DEBUG=true
PORT=8000

# 对话配置
CONVERSATION_SHORT_TERM_LIMIT=10
```

**注意**：`.env` 文件包含敏感信息，请确保它已添加到 `.gitignore` 中，不要提交到版本控制。

**数据库说明**：
- 默认使用 SQLite，无需额外安装数据库服务
- 如果需要使用 PostgreSQL，将 `DATABASE_URL` 改为：
  ```env
  DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/devsmart
  ```

#### 数据库初始化

```bash
# 创建数据库表
python -c "from models.database import init_database; import asyncio; asyncio.run(init_database())"
```

### 3. 前端设置

```bash
cd frontend
npm install
```

## 运行项目

### 方式一：使用启动脚本（推荐）

```bash
# 启动服务
./start.sh

# 停止服务
./stop.sh
```

### 方式二：手动启动

#### 启动后端

```bash
cd backend
source venv/bin/activate
python main.py
```

后端服务将运行在 `http://localhost:8000`

**API 文档**：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

#### 启动前端

```bash
cd frontend
npm run dev
```

前端服务将运行在 `http://localhost:5173`

### 方式三：使用 Docker Compose

```bash
docker-compose up -d
```

## API 接口

### 项目管理

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/projects` | 获取项目列表 |
| POST | `/api/projects` | 创建新项目 |
| GET | `/api/projects/{id}` | 获取项目详情 |
| DELETE | `/api/projects/{id}` | 删除项目 |

### 对话管理

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/conversations/{project_id}/messages` | 发送消息 |
| GET | `/api/conversations/{project_id}` | 获取对话历史 |

### PRD 管理

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/prd/{project_id}/generate` | 生成 PRD |
| GET | `/api/prd/{project_id}` | 获取 PRD 内容 |
| GET | `/api/prd/templates` | 获取 PRD 模板列表 |

### 技能系统

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/skills` | 列出所有技能 |
| GET | `/api/skills/{skill_id}` | 获取技能详情 |
| POST | `/api/skills/{skill_id}/execute` | 执行单个技能 |

### 工作流系统

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/workflows` | 列出所有工作流 |
| GET | `/api/workflows/{workflow_id}` | 获取工作流详情 |
| POST | `/api/workflows/{workflow_id}/execute` | 执行工作流 |

## 使用指导

### 1. 创建项目

1. 访问 `http://localhost:5173`
2. 点击「创建项目」
3. 在模板向导中填写：
   - **需求描述**：描述项目的核心需求
   - **后端技术选型**：选择后端语言（Python/Java/Go/Rust）
   - **前端技术选型**：选择前端框架（React/Vue/TypeScript）
   - **数据库选型**：选择数据库（PostgreSQL/MySQL/SQLite）
   - **部署形式**：选择部署方式（本地/Docker/云服务）

### 2. 需求对话

1. 进入项目详情页面
2. 在对话框中输入需求描述
3. 系统会自动分析需求完整度
4. 如果完整度不足，系统会生成追问问题
5. 持续回答问题直到需求完整度达到阈值

### 3. 生成 PRD

当需求完整度达到 75% 以上时：
- 点击「自动生成 PRD」按钮
- 或手动点击「生成 PRD」按钮（不受完整度限制）
- 系统会生成 Human PRD（Markdown）和 Machine PRD（YAML）

### 4. 查看 PRD

切换到「PRD」标签页查看生成的文档内容。

### 5. 技术选型

在「技术栈」标签页选择或推荐技术栈。

### 6. 下载 PRD

生成的 PRD 支持下载，包含两种格式：

- **Human PRD** (Markdown 格式) - 面向人类评审和阅读
- **Machine PRD** (YAML 格式) - 面向机器解析，结构化数据便于代码生成

下载后可将 PRD 文档交给任何 Code Agent（如 DevInfra、Cursor、GitHub Copilot 等）来生成代码。Machine PRD 的结构化格式特别适合作为 Code Agent 的输入，包含完整的需求规格、技术约束、API 定义等信息。

## RAG 三层记忆架构

DevSmart 采用基于向量数据库的三层记忆架构，提升 LLM 的上下文理解能力：

| 层级 | 内容 | 存储方式 | 检索方式 |
|------|------|---------|---------|
| **短期记忆** | 当前对话历史（最近 10 轮） | SQLite | 直接读取 |
| **中期记忆** | 对话摘要、关键决策点 | ChromaDB | 相似度检索 |
| **长期记忆** | 模板数据、PRD、技术文档 | ChromaDB | 语义检索 |

**工作原理**：
1. 创建项目时，模板数据自动存入长期记忆库
2. 对话过程中，系统实时检索相关记忆并注入上下文
3. 定期生成对话摘要存入中期记忆库
4. 当 RAG 服务不可用时，自动降级为传统系统提示模式

## 技能列表

### 需求分析技能

| 技能 ID | 名称 | 描述 |
|---------|------|------|
| `devsmart.requirement.analyze-gaps` | Analyze Requirement Gaps | 识别需求缺口并计算完整度 |
| `devsmart.requirement.generate-next-question` | Generate Next Question | 针对最高优先级缺口生成追问 |
| `devsmart.requirement.update-structured` | Update Structured Requirements | 将回答合并到结构化需求 |
| `devsmart.requirement.validate-readiness` | Validate Requirement Readiness | 判断需求是否足够生成 PRD |

### PRD 技能

| 技能 ID | 名称 | 描述 |
|---------|------|------|
| `devsmart.prd.generate-human` | Generate Human PRD | 生成面向人类的 Markdown PRD |
| `devsmart.prd.validate-human` | Validate Human PRD | 检查 PRD 必要章节 |
| `devsmart.prd.generate-machine` | Generate Machine PRD | 将 PRD 转为机器可读结构 |
| `devsmart.prd.validate-consistency` | Validate PRD Consistency | 检查引用完整性和验收覆盖率 |
| `devsmart.prd.scan` | PRD Scan | 扫描 PRD 并生成变更建议 |
| `devsmart.prd.delta` | PRD Delta | 生成 PRD 变更增量 |

### 技术技能

| 技能 ID | 名称 | 描述 |
|---------|------|------|
| `devsmart.tech.analyze-constraints` | Analyze Technical Constraints | 提取技术决策驱动因素 |
| `devsmart.tech.recommend-stack` | Recommend Tech Stack | 基于约束生成技术栈建议 |
| `devsmart.tech.validate-compatibility` | Validate Tech Stack Compatibility | 检查技术栈完整性和兼容性 |
| `devsmart.tech.generate-adr` | Generate Architecture Decision Record | 生成 ADR 文档 |

## 工作流列表

| 工作流 ID | 名称 | 步骤数 |
|-----------|------|--------|
| `devsmart.workflow.requirement-discovery` | 需求发现 | 4 |
| `devsmart.workflow.prd-generation` | PRD 生成 | 4 |
| `devsmart.workflow.tech-selection` | 技术选型 | 4 |

## 开发

### 后端开发

```bash
cd backend
source venv/bin/activate

# 运行测试
python -m pytest tests/ -v

# 格式检查
black .
isort .

# 类型检查
mypy .
```

### 前端开发

```bash
cd frontend

# 运行开发服务器
npm run dev

# 构建生产版本
npm run build

# 运行测试
npx playwright test
```

## 部署

### 后端部署

```bash
# 使用 Gunicorn
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000
```

### 前端部署

```bash
npm run build
# 将 dist 目录部署到静态服务器
```

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！