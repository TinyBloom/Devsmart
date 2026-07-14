# skill_prd_generate - 用户提示词

## 任务

根据对话历史生成双版本 PRD：
1. **Human PRD** (Markdown): 人类可读，用于用户审阅和确认
2. **Machine PRD** (YAML): 机器可读，供后续 Skill 消费

## 输入

**对话历史**: `{conversation_history}`

对话历史是一个列表，每条消息包含：
- `role`: "user" 或 "assistant"
- `content`: 消息内容
- `completeness_score`: 当前完整度评分（0-100）

## 需求完整度评分维度

| 维度 | 权重 | 说明 | 检测要求 |
|---|---|---|---|
| 核心功能 | 30% | 功能模块是否明确 | 至少 1 个功能模块 |
| 用户角色 | 15% | 目标用户是否定义 | 至少 1 个用户角色 |
| 数据实体 | 25% | 核心数据模型是否明确 | 至少 1 个数据实体 |
| 非功能需求 | 15% | 性能、安全等要求 | 性能、安全、扩展性等 |
| 外部集成 | 15% | 第三方服务集成 | API、支付、邮件等 |

**完整度 ≥ 80 分** 才能生成 PRD，否则需要继续追问。

## 输出格式

### Human PRD (Markdown)

```markdown
# {项目名称}

## 1. 产品概述
- **一句话描述**：{简洁的核心价值主张}
- **目标用户**：{用户角色描述}
- **核心价值**：{解决什么问题}

## 2. 功能模块
### 2.1 {模块名称}
- 功能描述
- 用户故事：As a {角色} I want {功能} so that {价值}

### 2.2 {模块名称}
...

## 3. 数据模型
### 3.1 {实体名称}
| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| id | UUID | 是 | 主键 |
| ... | ... | ... | ... |

### 3.2 {实体名称}
...

## 4. API 接口清单
| 接口 | 方法 | 路径 | 说明 |
|---|---|---|---|
| 获取列表 | GET | /api/{resource} | 获取资源列表 |
| 获取详情 | GET | /api/{resource}/{id} | 获取单个资源 |
| 创建 | POST | /api/{resource} | 创建资源 |
| 更新 | PUT | /api/{resource}/{id} | 更新资源 |
| 删除 | DELETE | /api/{resource}/{id} | 删除资源 |

## 5. 非功能需求
- **性能要求**：{描述}
- **安全要求**：{描述}
- **扩展性要求**：{描述}

## 6. 外部集成
- **{第三方服务}**：{集成目的}
```

### Machine PRD (YAML)

```yaml
project_name: "{项目名称}"
version: "1.0"
generated_at: "{时间戳}"

features:
  - name: "{模块名称}"
    description: "{模块描述}"
    user_stories:
      - as_a: "{角色}"
        i_want: "{功能}"
        so_that: "{价值}"
    priority: "{high|medium|low}"

data_models:
  - name: "{实体名称}"
    fields:
      - name: "字段名"
        type: "数据类型"
        required: true/false
        description: "字段说明"

api_endpoints:
  - path: "/api/{resource}"
    method: "GET|POST|PUT|DELETE"
    description: "接口描述"
    request_body: {}
    response: {}

non_functional:
  performance:
    expected_users: "{small|medium|large}"
    response_time: "{描述}"
  security:
    authentication: "{描述}"
    authorization: "{描述}"
  scalability:
    horizontal: true/false
    vertical: true/false

integrations:
  - name: "{第三方服务}"
    purpose: "{集成目的}"
    api_type: "{REST|GraphQL|SDK}"
```

## 生成规则

1. **提取关键信息**：
   - 从用户描述中提取核心需求
   - 从 LLM 追问中提取补充信息
   - 识别隐含的功能、数据、集成需求

2. **结构化输出**：
   - Human PRD 注重可读性和完整性
   - Machine PRD 注重机器解析的准确性

3. **版本管理**：
   - 每次生成新版本，版本号递增
   - human_prd_v1.md, human_prd_v2.md...
   - machine_prd_v1.yaml, machine_prd_v2.yaml...

4. **内容要求**：
   - 功能模块必须具体，避免模糊描述
   - 数据模型必须有明确字段和类型
   - API 接口必须有明确的路径和参数

## 注意事项

1. 如果对话历史中的信息不足以生成完整的 PRD，先使用占位符 `TBD`，后续可补充
2. 保持 Human PRD 和 Machine PRD 内容一致性
3. 确保 YAML 格式正确，可被后续 Skill 正确解析
