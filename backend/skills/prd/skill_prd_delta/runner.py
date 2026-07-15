"""
skill_prd_delta - Runner

为现有项目生成增量 PRD，支持新增功能和 Bug 修复
"""

import os
import yaml
import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class PRDDeltaRunner:
    """增量 PRD 生成 Skill Runner"""

    def __init__(self, project_dir: str, llm_service=None):
        self.project_dir = Path(project_dir)
        self.llm_service = llm_service
        self.skill_dir = Path(__file__).parent

    async def run(
        self,
        project_name: str,
        conversation_history: List[Dict[str, Any]],
        previous_prd_path: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            delta_type = self._classify_delta_type(conversation_history)
            
            previous_prd = {}
            if previous_prd_path and Path(previous_prd_path).exists():
                previous_prd = self._load_previous_prd(previous_prd_path)
            else:
                previous_prd = self._load_latest_prd()

            new_requirements = self._extract_new_requirements(conversation_history, previous_prd)
            
            completeness = self._calculate_completeness(new_requirements)
            
            if completeness["total_score"] < 60:
                return {
                    "status": "ERROR",
                    "message": f"需求完整度不足 ({completeness['total_score']}/100)，请继续补充信息",
                    "completeness": completeness,
                    "missing_dimensions": completeness["missing"]
                }

            delta_prd = self._generate_delta_prd(project_name, previous_prd, new_requirements, delta_type)
            
            human_prd = self._generate_human_prd(project_name, delta_prd, delta_type)
            machine_prd = self._generate_machine_prd(project_name, delta_prd, delta_type)

            version = self._get_next_version()
            
            docs_dir = self.project_dir / "docs"
            docs_dir.mkdir(parents=True, exist_ok=True)

            human_path = docs_dir / f"human_prd_v{version}.md"
            machine_path = docs_dir / f"machine_prd_v{version}.yaml"
            delta_path = docs_dir / f"delta_prd_v{version}.yaml"

            with open(human_path, 'w', encoding='utf-8') as f:
                f.write(human_prd)

            with open(machine_path, 'w', encoding='utf-8') as f:
                yaml.dump(machine_prd, f, allow_unicode=True, default_flow_style=False)

            with open(delta_path, 'w', encoding='utf-8') as f:
                yaml.dump(delta_prd, f, allow_unicode=True, default_flow_style=False)

            current_human = docs_dir / "human_prd_current.md"
            current_machine = docs_dir / "machine_prd_current.yaml"
            with open(current_human, 'w', encoding='utf-8') as f:
                f.write(human_prd)
            with open(current_machine, 'w', encoding='utf-8') as f:
                yaml.dump(machine_prd, f, allow_unicode=True, default_flow_style=False)

            logger.info(f"增量 PRD 已生成: human={human_path}, machine={machine_path}, delta={delta_path}")

            return {
                "status": "SUCCESS",
                "message": f"增量 PRD 生成成功 (版本 {version})",
                "version": version,
                "delta_type": delta_type,
                "completeness": completeness,
                "artifacts": [
                    {"file_path": str(human_path), "type": "human_prd"},
                    {"file_path": str(machine_path), "type": "machine_prd"},
                    {"file_path": str(delta_path), "type": "delta_prd"}
                ]
            }

        except Exception as e:
            logger.error(f"skill_prd_delta 执行失败: {e}")
            return {
                "status": "ERROR",
                "message": f"执行失败: {str(e)}"
            }

    def _classify_delta_type(self, conversation_history: List[Dict]) -> str:
        combined_text = ""
        for msg in conversation_history:
            combined_text += msg.get('content', '').lower()

        bug_keywords = ["bug", "错误", "修复", "问题", "异常", "崩溃", "bugfix"]
        feature_keywords = ["功能", "新增", "添加", "feature", "需求"]
        refactor_keywords = ["重构", "优化", "refactor", "性能"]
        enhance_keywords = ["改进", "增强", "升级", "enhance"]

        if any(k in combined_text for k in bug_keywords):
            return "BUG_FIX"
        elif any(k in combined_text for k in refactor_keywords):
            return "REFACTOR"
        elif any(k in combined_text for k in enhance_keywords):
            return "ENHANCEMENT"
        elif any(k in combined_text for k in feature_keywords):
            return "FEATURE_ADDITION"
        return "FEATURE_ADDITION"

    def _load_previous_prd(self, prd_path: str) -> Dict:
        try:
            with open(prd_path, 'r', encoding='utf-8') as f:
                if prd_path.endswith('.yaml') or prd_path.endswith('.yml'):
                    return yaml.safe_load(f)
                elif prd_path.endswith('.json'):
                    return json.load(f)
            return {}
        except Exception as e:
            logger.warning(f"加载历史 PRD 失败: {e}")
            return {}

    def _load_latest_prd(self) -> Dict:
        docs_dir = self.project_dir / "docs"
        if not docs_dir.exists():
            return {}

        latest_version = 0
        latest_path = None
        
        for f in docs_dir.glob("machine_prd_v*.yaml"):
            try:
                version_str = f.stem.replace("machine_prd_v", "")
                version = int(version_str)
                if version > latest_version:
                    latest_version = version
                    latest_path = f
            except ValueError:
                continue

        if latest_path:
            return self._load_previous_prd(str(latest_path))
        return {}

    def _extract_new_requirements(self, conversation_history: List[Dict], previous_prd: Dict) -> Dict[str, Any]:
        requirements = {
            "changes": [],
            "new_features": [],
            "bug_fixes": [],
            "enhancements": [],
            "refactors": [],
            "impacted_modules": [],
            "related_features": []
        }

        combined_text = ""
        for msg in conversation_history:
            if msg.get("role") == "user":
                combined_text += f"用户: {msg.get('content', '')}\n"
            elif msg.get("role") == "assistant":
                combined_text += f"助手: {msg.get('content', '')}\n"

        text_lower = combined_text.lower()

        if "bug" in text_lower or "错误" in text_lower or "修复" in text_lower:
            requirements["bug_fixes"].append({
                "description": "从对话中识别的 Bug 修复需求",
                "severity": "medium",
                "impact": []
            })

        if "功能" in text_lower or "新增" in text_lower or "feature" in text_lower:
            requirements["new_features"].append({
                "name": "从对话中识别的新功能",
                "description": "从对话历史中提取的功能需求",
                "priority": "medium",
                "user_stories": [],
                "impact": []
            })

        if "优化" in text_lower or "重构" in text_lower or "refactor" in text_lower:
            requirements["refactors"].append({
                "description": "从对话中识别的重构需求",
                "scope": [],
                "risk": "low"
            })

        if "改进" in text_lower or "增强" in text_lower or "enhance" in text_lower:
            requirements["enhancements"].append({
                "description": "从对话中识别的改进需求",
                "target": [],
                "expected_improvement": ""
            })

        if previous_prd:
            existing_features = previous_prd.get("features", [])
            for feature in existing_features:
                feature_name = feature.get("name", "").lower()
                if feature_name and feature_name in text_lower:
                    requirements["related_features"].append(feature.get("name"))

        return requirements

    def _calculate_completeness(self, requirements: Dict) -> Dict[str, Any]:
        weights = {
            "changes_description": 0.40,
            "impact_analysis": 0.30,
            "testing_plan": 0.30
        }

        scores = {}
        missing = []

        has_changes = any([
            requirements.get("new_features"),
            requirements.get("bug_fixes"),
            requirements.get("enhancements"),
            requirements.get("refactors")
        ])
        
        scores["changes_description"] = 100 if has_changes else 0
        if not has_changes:
            missing.append("changes_description")

        scores["impact_analysis"] = 100 if requirements.get("impacted_modules") else 50
        if not requirements.get("impacted_modules"):
            missing.append("impact_analysis")

        scores["testing_plan"] = 50

        total_score = sum(scores[k] * weights[k] for k in weights)

        return {
            "total_score": round(total_score, 1),
            "dimensions": scores,
            "missing": missing
        }

    def _generate_delta_prd(self, project_name: str, previous_prd: Dict, new_requirements: Dict, delta_type: str) -> Dict:
        delta_prd = {
            "project_name": project_name,
            "delta_type": delta_type,
            "version": self._get_next_version(),
            "generated_at": self._get_timestamp(),
            "previous_version": previous_prd.get("version", 0),
            "changes_summary": self._generate_changes_summary(new_requirements, delta_type),
            "new_features": new_requirements.get("new_features", []),
            "bug_fixes": new_requirements.get("bug_fixes", []),
            "enhancements": new_requirements.get("enhancements", []),
            "refactors": new_requirements.get("refactors", []),
            "impacted_modules": new_requirements.get("impacted_modules", []),
            "related_features": new_requirements.get("related_features", []),
            "backward_compatibility": "yes",
            "migration_notes": []
        }

        return delta_prd

    def _generate_changes_summary(self, requirements: Dict, delta_type: str) -> str:
        summaries = []
        
        if requirements.get("new_features"):
            summaries.append(f"新增 {len(requirements['new_features'])} 个功能")
        if requirements.get("bug_fixes"):
            summaries.append(f"修复 {len(requirements['bug_fixes'])} 个 Bug")
        if requirements.get("enhancements"):
            summaries.append(f"改进 {len(requirements['enhancements'])} 项功能")
        if requirements.get("refactors"):
            summaries.append(f"重构 {len(requirements['refactors'])} 个模块")
        
        if not summaries:
            return "无明确变更内容"
        
        return "; ".join(summaries)

    def _generate_human_prd(self, project_name: str, delta_prd: Dict, delta_type: str) -> str:
        delta_labels = {
            "FEATURE_ADDITION": "功能新增",
            "BUG_FIX": "Bug 修复",
            "REFACTOR": "代码重构",
            "ENHANCEMENT": "功能增强"
        }

        new_features_md = ""
        for i, feature in enumerate(delta_prd.get("new_features", []), 1):
            new_features_md += f"### 2.{i} {feature.get('name', '新功能')}\n"
            new_features_md += f"- {feature.get('description', '')}\n"

        bug_fixes_md = ""
        for i, bug in enumerate(delta_prd.get("bug_fixes", []), 1):
            bug_fixes_md += f"- **问题描述**：{bug.get('description', '')}\n"
            bug_fixes_md += f"  - **严重程度**：{bug.get('severity', 'medium')}\n"

        enhancements_md = ""
        for i, enhance in enumerate(delta_prd.get("enhancements", []), 1):
            enhancements_md += f"- **改进目标**：{enhance.get('description', '')}\n"

        refactors_md = ""
        for i, refactor in enumerate(delta_prd.get("refactors", []), 1):
            refactors_md += f"- **重构内容**：{refactor.get('description', '')}\n"

        impacted_modules = ", ".join(delta_prd.get("impacted_modules", ["待确认"]))
        related_features = ", ".join(delta_prd.get("related_features", ["无"]))

        prd = f"""# {project_name} - 增量 PRD

## 1. 变更概述
- **变更类型**：{delta_labels.get(delta_type, delta_type)}
- **版本号**：v{delta_prd.get('version')}
- **基于版本**：v{delta_prd.get('previous_version')}
- **生成时间**：{delta_prd.get('generated_at')}
- **变更摘要**：{delta_prd.get('changes_summary')}

## 2. 新增功能
{new_features_md if new_features_md else '_无新增功能_'}

## 3. Bug 修复
{bug_fixes_md if bug_fixes_md else '_无 Bug 修复_'}

## 4. 功能增强
{enhancements_md if enhancements_md else '_无功能增强_'}

## 5. 代码重构
{refactors_md if refactors_md else '_无代码重构_'}

## 6. 影响分析
- **受影响模块**：{impacted_modules}
- **关联功能**：{related_features}
- **向后兼容性**：{delta_prd.get('backward_compatibility', 'yes')}

## 7. 迁移说明
{delta_prd.get('migration_notes') if delta_prd.get('migration_notes') else '_无需迁移_'}
"""

        return prd

    def _generate_machine_prd(self, project_name: str, delta_prd: Dict, delta_type: str) -> Dict:
        return {
            "project_name": project_name,
            "version": delta_prd.get("version"),
            "delta_type": delta_type,
            "previous_version": delta_prd.get("previous_version"),
            "generated_at": delta_prd.get("generated_at"),
            "changes_summary": delta_prd.get("changes_summary"),
            "features": delta_prd.get("new_features", []),
            "bug_fixes": delta_prd.get("bug_fixes", []),
            "enhancements": delta_prd.get("enhancements", []),
            "refactors": delta_prd.get("refactors", []),
            "impacted_modules": delta_prd.get("impacted_modules", []),
            "related_features": delta_prd.get("related_features", []),
            "backward_compatibility": delta_prd.get("backward_compatibility"),
            "migration_notes": delta_prd.get("migration_notes", []),
            "data_models": [],
            "api_endpoints": [],
            "non_functional": {},
            "integrations": []
        }

    def _get_next_version(self) -> int:
        docs_dir = self.project_dir / "docs"
        if not docs_dir.exists():
            return 1

        existing_versions = []
        for f in docs_dir.glob("human_prd_v*.md"):
            try:
                version_str = f.stem.replace("human_prd_v", "")
                existing_versions.append(int(version_str))
            except ValueError:
                continue

        return max(existing_versions, default=0) + 1

    def _get_timestamp(self) -> str:
        return datetime.utcnow().isoformat() + "Z"


if __name__ == "__main__":
    import asyncio
    import sys

    async def main():
        if len(sys.argv) < 3:
            print("用法: python runner.py <project_name> <conversation_history_json>")
            sys.exit(1)

        project_name = sys.argv[1]
        history = json.loads(sys.argv[2])

        runner = PRDDeltaRunner(".")
        result = await runner.run(history, project_name)
        print(yaml.dump(result, allow_unicode=True))

    asyncio.run(main())