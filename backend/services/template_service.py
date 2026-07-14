"""
Template Service
PRD模板管理服务
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from config.settings import settings


class TemplateService:
    """PRD模板管理服务"""

    def __init__(self):
        self.templates_dir = settings.base_dir / "templates" / "prd"
        self._templates: Optional[Dict[str, Dict]] = None

    def _load_templates(self) -> Dict[str, Dict]:
        """加载所有模板文件"""
        if self._templates is not None:
            return self._templates

        templates = {}
        
        if not self.templates_dir.exists():
            return templates

        for file in self.templates_dir.glob("*.yaml"):
            if file.name == "schema.yaml":
                continue
            
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    template = yaml.safe_load(f)
                    template_id = template.get("id", file.stem)
                    templates[template_id] = template
            except Exception as e:
                print(f"加载模板 {file.name} 失败: {e}")

        self._templates = templates
        return templates

    def get_templates(self) -> List[Dict[str, Any]]:
        """获取所有模板列表"""
        templates = self._load_templates()
        return [
            {
                "id": template_id,
                "name": template.get("name", ""),
                "description": template.get("description", ""),
                "icon": template.get("icon", "📄"),
                "dimensions": template.get("dimensions", {})
            }
            for template_id, template in templates.items()
        ]

    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """获取指定模板"""
        templates = self._load_templates()
        return templates.get(template_id)

    def get_default_template(self) -> Dict[str, Any]:
        """获取默认模板（通用SaaS）"""
        templates = self._load_templates()
        return templates.get("general_saas", list(templates.values())[0]) if templates else {}

    def build_prompt_from_template(self, template: Dict[str, Any], project_name: str, 
                                  project_description: str, conversation_text: str) -> str:
        """根据模板构建PRD生成提示词"""
        sections = template.get("sections", [])
        
        # 构建章节结构描述
        sections_desc = []
        for section in sections:
            subsections_desc = []
            for subsection in section.get("subsections", []):
                hints = subsection.get("hints", [])
                hints_str = "\n".join(f"   - {hint}" for hint in hints) if hints else ""
                subsections_desc.append(f"   {subsection.get('title', '')}")
                if hints_str:
                    subsections_desc.append(f"     提示：")
                    subsections_desc.append(hints_str)
            
            sections_desc.append(f"- {section.get('title', '')}")
            if section.get("description"):
                sections_desc.append(f"  描述：{section.get('description')}")
            if subsections_desc:
                sections_desc.append("\n".join(subsections_desc))

        prompt = f"""请根据以下对话历史，使用"{template.get('name', '')}"模板生成一份完整的产品需求文档（PRD）。

项目名称：{project_name}
项目描述：{project_description or "无"}

对话历史：
{conversation_text}

请按照以下结构生成PRD，**必须在文档开头包含目录（Table of Contents）**：

## 目录
{chr(10).join(f"- [{section.get('title', '')}](#{section.get('title', '').replace('.', '').replace(' ', '-')})" for section in sections)}

{chr(10).join(sections_desc)}

请确保内容完整、清晰、专业。只输出PRD内容，不要包含其他说明文字。目录中的链接锚点要与章节标题对应。"""

        return prompt

    def get_template_dimensions(self, template_id: str) -> Dict[str, float]:
        """获取模板的维度权重"""
        template = self.get_template(template_id)
        if not template:
            return {
                "core_features": 30.0,
                "user_roles": 15.0,
                "data_entities": 25.0,
                "non_functional": 15.0,
                "integrations": 15.0
            }
        return {k: float(v) for k, v in template.get("dimensions", {}).items()}
