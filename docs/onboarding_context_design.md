# 基于轻量级 RAG 的三层记忆架构方案

## 一、问题背景

### 1.1 当前现状

在 DevSmart 系统中，用户在创建项目时会通过 Onboarding Wizard 填写一系列模板信息：

- **需求描述**（requirement\_description）
- **后端技术选型**（backend\_tech）
- **前端技术选型**（frontend\_tech）
- **数据库选择**（database）
- **部署形式**（deployment）

这些数据已存储在 `Project.onboarding_data` 字段中，但在后续与 LLM 的对话过程中，**这些关键信息没有被带入到对话上下文中**。

### 1.2 问题影响

- **LLM 缺乏项目背景**：每次对话时，LLM 只看到当前对话历史，完全不知道项目的技术栈和原始需求
- **回复质量受限**：无法给出与项目技术栈匹配的建议，生成的代码可能不符合项目约定
- **上下文断裂**：用户需要重复说明项目背景，降低对话效率

### 1.3 当前记忆机制的局限性

当前系统采用两层记忆机制：

| 层级   | 内容       | 存储方式                          | 局限性         |
| ---- | -------- | ----------------------------- | ----------- |
| 短期记忆 | 最近 N 轮对话 | 数据库表 `conversations`          | 无法扩展到大量历史   |
| 长期记忆 | 对话摘要     | 数据库表 `conversation_summaries` | 丢失细节，无法语义检索 |

**问题**：模板数据只是简单地作为系统提示注入，存在以下问题：

1. **Token 浪费**：模板数据每次都完整注入，即使大部分内容与当前问题无关
2. **信息过载**：LLM 需要处理大量无关信息，可能导致注意力分散
3. **无法扩展**：当项目文档增多时，简单的系统提示注入会超出 Token 限制
4. **缺乏语义理解**：无法根据用户问题的语义动态选择相关上下文

***

## 二、方案设计：三层记忆架构

### 2.1 核心思路

引入 **RAG（Retrieval-Augmented Generation）** 技术，构建三层记忆架构：

| 层级       | 内容                 | 存储方式   | 检索方式  |
| -------- | ------------------ | ------ | ----- |
| **短期记忆** | 当前对话历史（最近 5-10 轮）  | 关系型数据库 | 直接读取  |
| **中期记忆** | 对话摘要、关键决策点         | 向量数据库  | 相似度检索 |
| **长期记忆** | 模板数据、PRD、技术文档、代码规范 | 向量数据库  | 语义检索  |

### 2.2 RAG 技术选型

选择 **ChromaDB** 作为轻量级向量数据库，原因如下：

| 维度         | 说明                                   |
| ---------- | ------------------------------------ |
| **零部署**    | 嵌入式数据库，无需额外部署服务                      |
| **轻量级**    | 内存占用低，适合开发阶段                         |
| **API 友好** | Python API 简洁易用                      |
| **持久化**    | 支持本地文件存储，重启后数据不丢失                    |
| **可扩展**    | 未来可平滑迁移到 Pinecone、Milvus 等分布式向量数据库   |
| **默认嵌入模型** | 使用 all-MiniLM-L6-v2（约 80MB），首次使用自动下载 |

### 2.3 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户提问                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ConversationService                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ RAG检索      │  │ 摘要检索     │  │ 对话历史     │          │
│  │ (长期记忆)   │  │ (中期记忆)   │  │ (短期记忆)   │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼─────────────────┼─────────────────┼──────────────────┘
          │                 │                 │
          ▼                 ▼                 ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   ChromaDB      │ │   ChromaDB      │ │   SQLite        │
│  (长期记忆库)    │ │  (中期记忆库)    │ │  (对话历史表)    │
│ ├─ onboarding   │ │ ├─ 对话摘要     │ │ ├─ conversations │
│ ├─ PRD文档      │ │ ├─ 关键决策     │ │ └─ ...          │
│ ├─ 技术方案     │ │ └─ 需求变更     │ │                 │
│ └─ 代码规范     │ │                 │ │                 │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

***

## 三、核心实现

### 3.1 创建 RAG 服务

**文件路径**：`backend/services/rag_service.py`

#### 3.1.1 类结构

```python
class RAGService:
    def __init__(self):
        self._client = None                    # ChromaDB 客户端（延迟初始化）
        self._long_term_collection = None      # 长期记忆集合
        self._medium_term_collection = None    # 中期记忆集合
```

#### 3.1.2 关键方法

| 方法                           | 功能                  | 参数                             | 返回值                       |
| ---------------------------- | ------------------- | ------------------------------ | ------------------------- |
| `_get_client()`              | 延迟初始化 ChromaDB 客户端  | 无                              | ChromaDB PersistentClient |
| `_enforce_project_id()`      | 强制元数据包含 project\_id | project\_id, metadata          | 安全的 metadata              |
| `add_long_term_document()`   | 向长期记忆库添加文档          | project\_id, content, metadata | 文档 ID                     |
| `add_medium_term_document()` | 向中期记忆库添加文档          | project\_id, content, metadata | 文档 ID                     |
| `query_long_term()`          | 检索长期记忆库             | project\_id, query, top\_k     | 检索结果列表                    |
| `query_medium_term()`        | 检索中期记忆库             | project\_id, query, top\_k     | 检索结果列表                    |
| `delete_project_documents()` | 删除项目所有记忆文档          | project\_id                    | 无                         |
| `_format_results()`          | 格式化检索结果             | ChromaDB 查询结果                  | 格式化列表                     |
| `get_collection_stats()`     | 获取集合统计信息            | collection\_type               | 统计字典                      |

#### 3.1.3 异步处理策略

由于 ChromaDB Python 客户端是同步的，所有方法都使用 `asyncio.to_thread()` 包装，避免阻塞 FastAPI 事件循环：

```python
results = await asyncio.to_thread(
    self._long_term_collection.query,
    query_texts=[query],
    n_results=top_k,
    where={"project_id": project_id}
)
```

#### 3.1.4 降级策略

当 RAG 服务不可用时（如初始化失败、数据库文件损坏），所有查询方法返回空列表，由调用方处理回退逻辑：

```python
try:
    # RAG 检索逻辑
    ...
except Exception as e:
    logger.warning(f"[RAG 检索失败] project_id={project_id}, error={str(e)}")
    return []  # 降级为空结果
```

### 3.2 修改 `ConversationService`

**文件路径**：`backend/services/conversation_service.py`

#### 3.2.1 修改 `_get_conversation_context` 方法

```python
async def _get_conversation_context(
    self,
    project_id: str,
    phase: str,
    user_input: str = "",
    project: Optional[Project] = None
) -> List[Dict]:
    """
    获取对话上下文（三层记忆策略）

    Args:
        project_id: 项目 ID
        phase: 阶段
        user_input: 用户当前输入（用于 RAG 检索）
        project: 项目对象（用于降级回退时获取 onboarding_data）

    Returns:
        对话历史列表（长期记忆 + 中期记忆 + 短期记忆）
    """
    context = []
    rag_service = RAGService()

    # 1. 长期记忆：RAG 检索项目知识库
    rag_has_results = False
    if user_input:
        long_term_results = await rag_service.query_long_term(project_id, user_input)
        if long_term_results:
            rag_has_results = True
            for result in long_term_results:
                doc_type = result["metadata"].get("type", "文档")
                context.append({
                    "role": "system",
                    "content": f"【项目知识 - {doc_type}】\n{result['content']}"
                })

    # 降级回退：如果 RAG 没有返回结果，使用 onboarding_data 作为系统提示
    if not rag_has_results and project and project.onboarding_data:
        system_prompt = self._format_onboarding_as_system_prompt(project.onboarding_data)
        context.append({
            "role": "system",
            "content": system_prompt
        })

    # 2. 中期记忆：RAG 检索对话摘要
    if user_input:
        medium_term_results = await rag_service.query_medium_term(project_id, user_input)
        for result in medium_term_results:
            context.append({
                "role": "system",
                "content": f"【历史对话摘要】\n{result['content']}"
            })

    # 3. 短期记忆：最近 N 轮对话
    short_term_limit = settings.conversation_short_term_limit
    recent_query = select(Conversation).where(
        Conversation.project_id == project_id,
        Conversation.phase == phase
    ).order_by(Conversation.created_at.desc()).limit(short_term_limit)
    recent_result = await self.db.execute(recent_query)
    recent_conversations = recent_result.scalars().all()

    for conv in reversed(recent_conversations):
        context.append({
            "role": conv.role,
            "content": conv.content
        })

    return context
```

#### 3.2.2 添加 `_format_onboarding_as_system_prompt` 方法

```python
def _format_onboarding_as_system_prompt(self, onboarding_data: Dict) -> str:
    """
    将 onboarding_data 格式化为系统提示

    Args:
        onboarding_data: 项目的 onboarding 数据字典

    Returns:
        格式化后的系统提示文本
    """
    parts = [
        "【项目背景信息】",
        f"需求描述：{onboarding_data.get('requirement_description', '未提供')}",
        f"后端技术：{onboarding_data.get('backend_tech', '未选择')}",
        f"前端技术：{onboarding_data.get('frontend_tech', '未选择')}",
        f"数据库：{onboarding_data.get('database', '未选择')}",
        f"部署形式：{onboarding_data.get('deployment', '未选择')}",
        "",
        "请基于以上项目背景进行回答。"
    ]
    return "\n".join(parts)
```

#### 3.2.3 修改 `send_message` 方法中的 `all_conversations` 构建

```python
# 修改前
all_conversations = conversation_history + [{"role": "user", "content": content}]

# 修改后
rag_service = RAGService()

# 注入长期记忆（RAG 检索结果）
long_term_results = await rag_service.query_long_term(project_id, content)
rag_context = []
rag_has_results = False

if long_term_results:
    rag_has_results = True
    for result in long_term_results:
        doc_type = result["metadata"].get("type", "文档")
        rag_context.append({
            "role": "system",
            "content": f"【项目知识 - {doc_type}】\n{result['content']}"
        })

# 降级回退：如果 RAG 没有返回结果，使用 onboarding_data 作为系统提示
if not rag_has_results and project and project.onboarding_data:
    system_prompt = self._format_onboarding_as_system_prompt(project.onboarding_data)
    rag_context.append({
        "role": "system",
        "content": system_prompt
    })

all_conversations = rag_context + conversation_history + [{"role": "user", "content": content}]
```

### 3.3 在项目创建时将模板数据存入 RAG

**文件路径**：`backend/services/project_service.py`

```python
async def create_project(
    self, 
    name: str, 
    description: Optional[str] = None,
    project_type: Optional[str] = ProjectType.GREENFIELD,
    source_path: Optional[str] = None,
    onboarding_data: Optional[Dict] = None
) -> Project:
    """
    创建新项目（修改后）
    """
    # 创建项目（原有逻辑）
    project = Project(
        name=name, 
        description=description,
        project_type=project_type,
        source_path=source_path,
        onboarding_data=onboarding_data
    )
    self.db.add(project)
    try:
        await self.db.commit()
        await self.db.refresh(project)
    except IntegrityError:
        await self.db.rollback()
        raise ValueError(f"项目名称 '{name}' 已存在")

    # 将 onboarding_data 存入 RAG（新增）
    if project.onboarding_data:
        rag_service = RAGService()
        doc_content = self._format_onboarding_document(project.onboarding_data)
        await rag_service.add_long_term_document(
            project_id=str(project.id),
            content=doc_content,
            metadata={
                "type": "onboarding",
                "phase": "prd",
                "created_at": datetime.utcnow().isoformat()
            }
        )

    # 创建项目目录和 project.json（原有逻辑）
    await self._create_project_files(project)

    return project

def _format_onboarding_document(self, onboarding_data: Dict) -> str:
    """
    将 onboarding_data 格式化为 RAG 文档
    """
    doc_parts = [
        "项目需求描述：",
        onboarding_data.get("requirement_description", "未提供"),
        "",
        "后端技术选型：",
        onboarding_data.get("backend_tech", "未选择"),
        "",
        "前端技术选型：",
        onboarding_data.get("frontend_tech", "未选择"),
        "",
        "数据库选型：",
        onboarding_data.get("database", "未选择"),
        "",
        "部署形式：",
        onboarding_data.get("deployment", "未选择"),
    ]
    return "\n".join(doc_parts)
```

### 3.4 修改摘要生成逻辑

**文件路径**：`backend/services/conversation_service.py`

```python
async def _check_and_generate_summary(self, project_id: str, phase: str):
    """
    检查是否需要生成对话摘要（修改后）
    """
    # 获取当前对话总数（原有逻辑）
    count_query = select(Conversation).where(
        Conversation.project_id == project_id,
        Conversation.phase == phase
    )
    count_result = await self.db.execute(count_query)
    all_conversations = count_result.scalars().all()

    # 检查是否达到摘要触发条件（原有逻辑）
    trigger_interval = settings.summary_trigger_interval
    should_generate_summary = len(all_conversations) % trigger_interval == 0

    if should_generate_summary:
        # 获取最近的对话用于生成摘要（原有逻辑）
        recent_conversations = all_conversations[-trigger_interval:]
        conversation_list = [
            {"role": c.role, "content": c.content}
            for c in recent_conversations
        ]

        # 调用 LLM 生成摘要（原有逻辑）
        settings_service = SettingsService(self.db)
        llm_config = await settings_service.get_effective_llm_config()
        client = LLMClient(llm_config)
        summary_content = await client.generate_summary(conversation_list)

        # 保存到数据库（原有逻辑）
        last_conv = recent_conversations[-1]
        summary = ConversationSummary(
            project_id=project_id,
            phase=phase,
            summary=summary_content,
            covers_up_to_id=last_conv.id,
            created_at=datetime.utcnow()
        )
        self.db.add(summary)
        await self.db.commit()

        # 存入中期记忆库（新增）
        rag_service = RAGService()
        await rag_service.add_medium_term_document(
            project_id=str(project_id),
            content=summary_content,
            metadata={
                "type": "conversation_summary",
                "phase": phase,
                "covers_up_to_id": str(last_conv.id),
                "created_at": datetime.utcnow().isoformat()
            }
        )
```

***

## 四、上下文层次结构

### 4.1 最终注入到 LLM 的消息列表

```python
[
    # 长期记忆：RAG 检索的项目知识库
    {
        "role": "system",
        "content": "【项目知识 - onboarding】\n项目需求描述：开发一个在线商城...\n后端技术选型：python..."
    },
    
    # 中期记忆：RAG 检索的对话摘要
    {
        "role": "system", 
        "content": "【历史对话摘要】\n用户希望实现一个电商平台的订单管理功能，讨论了订单状态流转..."
    },
    
    # 短期记忆：系统提示
    {
        "role": "system", 
        "content": "你是一个专业的软件需求分析助手。你的任务是帮助用户梳理软件需求..."
    },
    
    # 短期记忆：对话历史
    {
        "role": "user", 
        "content": "如何设计订单表的数据库结构？"
    },
    {
        "role": "assistant", 
        "content": "根据项目需求，订单表需要包含以下字段：..."
    },
    
    # 当前输入
    {
        "role": "user", 
        "content": "这个订单表需要支持什么索引？"
    }
]
```

### 4.2 上下文优先级说明

| 优先级 | 上下文类型     | 检索方式 | 作用              |
| --- | --------- | ---- | --------------- |
| 1   | 长期记忆（RAG） | 语义检索 | 项目基础信息，精准匹配当前问题 |
| 2   | 中期记忆（RAG） | 语义检索 | 对话摘要，关联历史决策     |
| 3   | 系统提示      | 直接注入 | LLM 角色定义和行为约束   |
| 4   | 短期记忆      | 直接读取 | 当前对话上下文，保持连贯性   |

***

## 五、方案优势

### 5.1 技术优势

| 维度       | 说明                                     |
| -------- | -------------------------------------- |
| **精准检索** | 基于向量相似度匹配，只注入与当前问题相关的信息                |
| **语义理解** | 理解问题的深层含义，支持同义词和语义相关检索                 |
| **可扩展性** | 支持海量文档，不受 Token 限制                     |
| **动态更新** | 文档更新后可重新索引，无需修改代码                      |
| **零部署**  | 使用 ChromaDB 嵌入式数据库，无需额外部署服务            |
| **向后兼容** | 如果 RAG 服务不可用，降级为原有逻辑                   |
| **异步友好** | 使用 asyncio.to\_thread() 包装同步操作，不阻塞事件循环 |

### 5.2 业务优势

| 维度           | 说明                  |
| ------------ | ------------------- |
| **回复准确性**    | LLM 回复基于相关上下文，更加精准  |
| **Token 效率** | 只注入相关信息，减少 Token 浪费 |
| **用户体验**     | 用户无需重复说明项目背景        |
| **开发效率**     | 生成的代码符合项目约定，减少返工    |

***

## 六、集成点排查

### 6.1 当前系统中的 LLM 调用链路

#### 6.1.1 链路一：常规对话（`_generate_llm_response`）

```python
# conversation_service.py:111-115
assistant_response = await self._generate_llm_response(
    conversation_history,    # ← 来自 _get_conversation_context（已包含 RAG 检索）
    content,
    project.name if project else "未命名项目"
)
```

**状态**：✅ 通过修改 `_get_conversation_context` 可覆盖此链路

#### 6.1.2 链路二：首次对话特殊路径

```python
# conversation_service.py:268-273
if len([m for m in conversation_history if m["role"] != "system"]) == 0:
    question_result = self.questioning_strategy.generate_next_question(
        [{"role": "user", "content": user_input}],
        project_name
    )
    return {"content": question_result["question"]}
```

**问题**：当判断为第一次对话时，直接使用 `QuestioningStrategy` 生成问题，**绕过了 LLM 调用**。

**解决方案**：修改 `QuestioningStrategy.generate_next_question` 方法，接收 RAG 检索结果作为参考：

```python
def generate_next_question(self, conversation: List[Dict], project_name: str, context_info: str = "") -> Dict:
    """
    生成下一个问题（修改后）
    
    Args:
        conversation: 对话历史
        project_name: 项目名称
        context_info: RAG 检索到的项目上下文信息
    
    Returns:
        {"question": "生成的问题"}
    """
    # 在生成问题时参考 context_info
    # ...
```

#### 6.1.3 链路三：Skill Runner 调用

```python
# conversation_service.py:118-131
all_conversations = conversation_history + [{"role": "user", "content": content}]

context = SkillContext(project_id=project_id)

analyze_result = await self.skill_runner.run(
    "devsmart.requirement.analyze-gaps",
    {
        "idea": content,
        "conversation": all_conversations,    # ← 需要注入 RAG 上下文
        "requirements": {},
    },
    context,
)
```

**解决方案**：在构建 `all_conversations` 时，先进行 RAG 检索并注入：

```python
# 修改后
rag_service = RAGService()
long_term_results = rag_service.query_long_term(project_id, content)

rag_context = []
for result in long_term_results:
    doc_type = result["metadata"].get("type", "文档")
    rag_context.append({
        "role": "system",
        "content": f"【项目知识 - {doc_type}】\n{result['content']}"
    })

all_conversations = rag_context + conversation_history + [{"role": "user", "content": content}]
```

#### 6.1.4 链路四：摘要生成

```python
# conversation_service.py:324
summary_content = await client.generate_summary(conversation_list)
```

**分析**：摘要生成的输入是最近的对话列表，不包含 RAG 上下文。这是合理的，因为摘要的目的是总结对话内容。但生成的摘要需要存入中期记忆库。

### 6.2 需要同步修改的文件清单

| 文件路径                                       | 修改内容                                          | 优先级 |
| ------------------------------------------ | --------------------------------------------- | --- |
| `backend/services/rag_service.py`          | **新增**：创建 RAG 向量检索服务                          | 高   |
| `backend/services/conversation_service.py` | 修改 `_get_conversation_context`，集成 RAG 检索      | 高   |
| `backend/services/conversation_service.py` | 修改 `send_message` 中的 `all_conversations` 构建逻辑 | 高   |
| `backend/services/conversation_service.py` | 修改 `_check_and_generate_summary`，存入中期记忆库      | 高   |
| `backend/services/project_service.py`      | 创建项目时将 onboarding\_data 存入 RAG                | 高   |
| `backend/services/project_service.py`      | 添加 `_format_onboarding_document` 方法           | 高   |
| `backend/services/conversation_service.py` | 添加 `_format_onboarding_as_system_prompt` 方法   | 高   |
| `backend/services/questioning_strategy.py` | 修改 `generate_next_question`，接收 RAG 上下文        | 中   |
| `backend/requirements.txt`                 | 添加 chromadb 依赖                                | 高   |

***

## 七、实施步骤

### 7.1 第一阶段：基础实现

| 步骤 | 任务                                         | 状态    |
| -- | ------------------------------------------ | ----- |
| 1  | 添加 chromadb 依赖到 requirements.txt           | ✅ 已完成 |
| 2  | 创建 `rag_service.py`，实现 RAG 服务              | ✅ 已完成 |
| 3  | 修改 `project_service.py`，创建项目时存入 RAG        | ✅ 已完成 |
| 4  | 修改 `conversation_service.py`，集成 RAG 检索到上下文 | ✅ 已完成 |
| 5  | 修改摘要生成逻辑，存入中期记忆库                           | ✅ 已完成 |
| 6  | 测试验证，确保 LLM 回复参考了 RAG 检索结果                 | ⚠️ 部分验证 |

### 7.2 第二阶段：优化迭代

| 步骤 | 任务                                  | 优先级 |
| -- | ----------------------------------- | --- |
| 7  | 修改 `QuestioningStrategy`，支持 RAG 上下文 | 中   |
| 8  | 支持更多文档类型（PRD、技术文档）                  | 中   |
| 9  | 实现文档上传和解析功能                         | 低   |
| 10 | 添加记忆更新和删除机制                         | 中   |

### 7.3 第三阶段：完善记忆体系

| 步骤 | 任务                      | 优先级 |
| -- | ----------------------- | --- |
| 11 | 实现三层记忆的协同工作策略           | 中   |
| 12 | 添加记忆遗忘机制（定期清理过期摘要）      | 低   |
| 13 | 支持多项目间的知识共享             | 低   |
| 14 | 迁移到分布式向量数据库（如 Pinecone） | 低   |

***

## 八、测试验证方案

### 8.1 测试场景

**场景 1**：创建项目时选择 Python + React + PostgreSQL

**预期结果**：

- 在对话中询问"如何设计用户认证"时，RAG 应检索到技术选型信息
- LLM 应推荐基于 Python（如 FastAPI）和 React 的认证方案
- 代码示例应符合选定的技术栈

**场景 2**：创建项目时填写了需求描述"开发一个在线商城"

**预期结果**：

- 在对话中询问"需要哪些核心功能"时，RAG 应检索到需求描述
- LLM 应基于电商场景进行回答
- 不应要求用户重复说明项目类型

**场景 3**：多轮对话后的摘要检索

**预期结果**：

- 当对话达到摘要触发条件时，摘要应自动存入中期记忆库
- 后续对话中，RAG 应能检索到相关的历史对话摘要

**场景 4**：RAG 服务不可用的降级测试

**预期结果**：

- 当 ChromaDB 初始化失败时，系统应自动降级使用 onboarding\_data
- 对话功能不应受到影响

### 8.2 验证方法

1. 创建测试项目，填写完整的 onboarding 数据
2. 在对话中提出与技术选型相关的问题
3. 检查 RAG 检索结果是否包含相关信息
4. 检查 LLM 回复是否参考了检索结果
5. 进行多轮对话，验证摘要生成和检索功能
6. 手动删除 rag\_db 目录，验证降级逻辑

***

## 九、注意事项

### 9.1 Token 消耗

- RAG 检索结果会增加 Token 消耗，但比完整注入模板数据更高效
- 建议限制每次检索的文档数量（top\_k=3）
- 建议对检索结果进行截断处理

### 9.2 数据更新

- 如果用户修改了 onboarding\_data，需要更新 RAG 中的文档
- 建议在数据更新时删除旧文档并重新插入

### 9.3 兼容性

- 旧项目可能没有 RAG 文档，需要处理空检索结果的情况
- 确保方案向后兼容，不影响现有项目的正常使用

### 9.4 RAG 服务可用性

- 需要处理 RAG 服务不可用的情况（如数据库文件损坏）
- 建议添加降级逻辑，当 RAG 服务失败时使用原有逻辑

### 9.5 依赖安装

需要在 `requirements.txt` 中添加：

```txt
chromadb>=0.4.0
```

首次安装时会自动下载嵌入模型（约 80MB），需要确保网络通畅。

### 9.6 向量数据库存储

- ChromaDB 默认将数据存储在 `./rag_db` 目录下
- 需要将 `rag_db/` 添加到 `.gitignore`，避免提交到版本控制
- 生产环境建议使用独立的向量数据库服务

***

## 十、总结

本方案引入 **RAG 技术**，构建了三层记忆架构：

1. **短期记忆**：当前对话历史，保持对话连贯性
2. **中期记忆**：对话摘要，关联历史决策
3. **长期记忆**：模板数据、PRD、技术文档等，通过语义检索精准匹配

相比简单的系统提示注入方案，RAG 方案具有以下优势：

- **精准检索**：只注入与当前问题相关的信息
- **语义理解**：支持同义词和语义相关检索
- **可扩展性**：支持海量文档，不受 Token 限制
- **零部署**：使用 ChromaDB 嵌入式数据库
- **异步友好**：不阻塞 FastAPI 事件循环
- **降级策略**：RAG 服务不可用时自动回退

实施步骤清晰，从基础实现到优化迭代逐步推进，适合当前项目的发展阶段。
