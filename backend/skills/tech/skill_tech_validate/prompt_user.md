# skill_tech_validate - 用户提示词

## 任务

验证用户选择的技术栈是否与 Machine PRD 中的需求相匹配，检查潜在的冲突和问题。

## 输入

1. **Machine PRD 内容**: `{machine_prd_content}`
2. **用户选择的技术栈**:
   - 后端: `{backend}`
   - 前端: `{frontend}`
   - 数据库: `{database}`
   - 缓存: `{cache}`
   - 部署方式: `{deployment}`
   - CI/CD: `{cicd}`

## 验证规则

### 1. 后端框架验证

| 规则 ID | 条件 | 严重程度 | 消息 |
|---|---|---|---|
| ai_mismatch | 有 AI 需求但选择非 Python | warning | 检测到 AI 相关需求，建议考虑 Python 作为后端语言 |
| rust_small_project | Rust + 小规模项目 | high | Rust 学习曲线陡峭，编译时间长，不适合快速原型开发 |
| python_large_scale | Python + 大规模系统 | medium | Python FastAPI 在超大规模系统中的性能可能不足 |
| high_concurrency_python | 高并发要求 + Python | high | Python (GIL) 在高并发场景下性能受限 |
| java_urgent_timeline | Java + 紧急时间线 | medium | Java 开发周期相对较长，可能影响交付时间 |

### 2. 数据库验证

| 规则 ID | 条件 | 严重程度 | 消息 |
|---|---|---|---|
| elasticsearch_overkill | ES + 简单项目 | low | Elasticsearch 资源消耗大，运维复杂，简单项目可能不需要 |
| mongodb_transaction | MongoDB + 强事务需求 | high | MongoDB 事务能力有限，强一致性场景不推荐 |

### 3. 部署方式验证

| 规则 ID | 条件 | 严重程度 | 消息 |
|---|---|---|---|
| k8s_small_project | K8s + 功能少于 5 个 | low | Kubernetes 复杂度较高，对于简单项目可能过度设计 |
| spring_cloud_non_java | Spring Cloud + 非 Java | high | Spring Cloud 主要针对 Java 技术栈 |

### 4. 兼容性矩阵

| 组合 | 兼容性 | 说明 |
|---|---|---|
| React + 任何后端 | ✓ | 完全兼容 |
| Vue + 任何后端 | ✓ | 完全兼容 |
| Svelte + 任何后端 | ✓ | 完全兼容 |
| PostgreSQL + 任何后端 | ✓ | 完全兼容 |
| MySQL + 任何后端 | ✓ | 完全兼容 |
| MongoDB + 任何后端 | ✓ | 完全兼容 |
| Redis + 任何后端 | ✓ | 完全兼容 |
| K8s + 任何后端 | ✓ | 完全兼容 |
| Spring Cloud + 非 Java | ✗ | Spring Cloud 主要针对 Java |

## 输出要求

请以 YAML 格式输出验证报告：

```yaml
validation_report:
  generated_at: "2026-06-29T10:00:00Z"
  project_name: "my-project"

  status: "warning"  # passed | warning | error
  summary: "发现 1 个潜在问题，请仔细评估"

  warnings:
    - id: "ai_mismatch"
      severity: "warning"
      message: "检测到 AI 相关需求，建议考虑 Python 作为后端语言"
      suggestion: "如果团队有 Python 经验，建议使用 Python FastAPI 以获得更好的 AI 集成体验"

  suggestions:
    - message: "您的技术栈选择基本合理，以上警告仅供参考"

  compatibility_matrix:
    backend_frontend: "compatible"
    backend_database: "compatible"
    backend_deployment: "compatible"
    all_compatible: true
```

## 判断标准

- **status: passed**: 无任何警告和建议
- **status: warning**: 有警告（warning）或建议（suggestion），但无高严重程度问题
- **status: error**: 有高（high）严重程度的警告

## 注意事项

1. 验证应该基于 Machine PRD 中的实际需求，而非主观臆断
2. 低严重程度的警告可以忽略，但应该在报告中体现
3. 如果所有检查都通过，status 应为 "passed"
4. 最终输出必须是可以直接使用的 `tech_validation.yaml` 文件
