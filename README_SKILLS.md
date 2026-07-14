# DevSmart Skills 基础实现

这是一个可覆盖到 DevSmart 仓库根目录的补丁包，新增 12 个可版本化 Skill、统一 Registry/Runner、三个示例 Workflow 和最小测试。

## Skill 清单

### Requirement

1. `devsmart.requirement.analyze-gaps@1.0.0`
2. `devsmart.requirement.generate-next-question@1.0.0`
3. `devsmart.requirement.update-structured@1.0.0`
4. `devsmart.requirement.validate-readiness@1.0.0`

### PRD

5. `devsmart.prd.generate-human@1.0.0`
6. `devsmart.prd.validate-human@1.0.0`
7. `devsmart.prd.generate-machine@1.0.0`
8. `devsmart.prd.validate-consistency@1.0.0`

### Tech

9. `devsmart.tech.analyze-constraints@1.0.0`
10. `devsmart.tech.recommend-stack@1.0.0`
11. `devsmart.tech.validate-compatibility@1.0.0`
12. `devsmart.tech.generate-adr@1.0.0`

## 安装

将本包内容复制到仓库根目录。确保后端依赖包含：

```text
pydantic>=2
PyYAML
pytest
pytest-asyncio
```

## 接入现有 LiteLLM 服务

实现 `LLMGateway` 协议：

```python
from backend.skills.models import LLMResponse

class DevSmartLLMGateway:
    async def generate_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        output_schema: dict,
        temperature: float = 0.2,
    ) -> LLMResponse:
        # 在这里调用现有 LiteLLM service，并启用 JSON/structured output。
        data = await existing_llm_service.generate_json(...)
        return LLMResponse(data=data)
```

运行 Skill：

```python
from backend.skills import SkillContext, SkillRunner, build_default_registry

runner = SkillRunner(build_default_registry())
result = await runner.run(
    "devsmart.requirement.validate-readiness",
    {"requirements": requirements},
    SkillContext(project_id=project_id, llm=llm_gateway),
)
```

## 设计约束

- Workflow 决定步骤顺序，Skill 不推进全局状态。
- Skill 输入和输出均由 Pydantic 校验。
- LLM Skill 只生成结构化 JSON。
- Validator 优先采用确定性规则。
- Artifact 只返回草稿；正式落盘应由统一 Artifact Service 负责。
- Workflow YAML 当前是编排契约示例，尚未包含表达式执行器。

## 测试

```bash
pytest -q tests/test_skills.py
```
