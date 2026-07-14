# skill_tech_recommend - 用户提示词

## 任务

根据项目的 Machine PRD 内容，分析需求特征，推荐 1-3 套最合适的技术方案。

## 输入

- `{machine_prd_content}`: Machine PRD 的完整内容

## 推荐维度

每套方案必须包含以下维度：

1. **后端框架** (Backend Framework)
   - 候选：`Rust + Actix-web`, `Java + Spring Boot`, `Java + Quarkus`, `Go + Gin`, `Python + FastAPI`
   - 评估指标：性能、复杂度、上市时间、生态成熟度

2. **前端框架** (Frontend Framework)
   - 候选：`React + Vite`, `Vue + Vite`, `Svelte`
   - 评估指标：生态丰富度、学习曲线、组件复用性

3. **数据库** (Database)
   - 候选：`PostgreSQL`, `MySQL`, `MongoDB`
   - 评估指标：事务能力、扩展性、JSON 支持

4. **缓存** (Cache)
   - 候选：`Redis`
   - 评估指标：性能、数据结构丰富度

5. **部署方式** (Deployment)
   - 候选：`Kubernetes + Helm`, `Kubernetes + Go Operator`, `Spring Cloud`
   - 评估指标：复杂度、自动化程度、运维成本

6. **CI/CD** (CI/CD Tool)
   - 候选：`GitHub Actions`, `Jenkins`
   - 评估指标：易用性、插件生态、集成能力

## 输出要求

请以 YAML 格式输出技术方案推荐：

```yaml
tech_options:
  - name: "快速原型方案"
    description: "最适合快速交付和 AI 集成的方案"
    backend:
      framework: "Python + FastAPI"
      orm: "SQLAlchemy"
      pros:
        - "Python 语法简洁，开发效率极高"
        - "AI/ML 集成最方便"
        - "FastAPI 自动生成 OpenAPI 文档"
      cons:
        - "性能不如 Go/Rust"
        - "GIL 限制多线程性能"
      complexity: "低"
      performance: "中"
      time_to_market: "很快"
    frontend:
      framework: "React + Vite"
      ui_library: "shadcn/ui"
    database:
      primary: "PostgreSQL"
      cache: "Redis"
    deployment:
      method: "Kubernetes + Helm"
    cicd:
      tool: "GitHub Actions"
    reason: "AI 集成需求强烈，Python 是 AI/ML 领域的首选语言"
    tradeoffs: |
      优点：开发效率高，AI 集成方便，TypeScript 支持好
      缺点：性能中等，GIL 限制多线程
      复杂度：低
      性能：中
      上市时间：很快
    risk: "高并发场景可能需要额外优化"
    suitability_score: 85

  - name: "高性能微服务方案"
    # ... 第二套方案

  - name: "企业级稳定方案"
    # ... 第三套方案（可选）
```

## 推荐逻辑

根据以下需求特征进行推荐：

| 需求特征 | 推荐方案 |
|---|---|
| 有 AI/ML 需求 | Python FastAPI 优先 |
| 团队无特殊技术栈经验 | Python FastAPI 或 Go Gin |
| 追求高性能 | Go Gin 或 Rust Actix |
| 企业级大型系统 | Java Spring Boot |
| 云原生部署 | Java Quarkus 或 Go Gin |
| 时间紧迫 | Python FastAPI |
| 大规模系统 | Java Spring Boot 或 Go Gin |

## 权衡分析指南

### 后端框架对比

| 框架 | 性能 | 复杂度 | 上市时间 | 适用场景 |
|---|---|---|---|---|
| Rust + Actix | 极高 | 高 | 慢 | 高性能核心服务 |
| Java + Spring | 中 | 中 | 中 | 企业级系统 |
| Java + Quarkus | 高 | 中 | 快 | 云原生微服务 |
| Go + Gin | 高 | 低 | 快 | 微服务 |
| Python + FastAPI | 中 | 低 | 很快 | AI/快速原型 |

### 数据库对比

| 数据库 | 事务 | JSON | 扩展性 | 适用场景 |
|---|---|---|---|---|
| PostgreSQL | 强 | 好 | 中 | 几乎所有业务 |
| MySQL | 中 | 一般 | 好 | 互联网产品 |
| MongoDB | 弱 | 很好 | 好 | 文档存储 |

## 注意事项

1. 每套方案必须包含详细的权衡分析
2. 推荐理由必须基于需求特征，不能盲目推荐热门技术
3. 如果项目有明显特征（如 AI 需求），优先考虑相关技术
4. 最终输出必须是可以直接使用的 `tech_options.yaml` 文件
