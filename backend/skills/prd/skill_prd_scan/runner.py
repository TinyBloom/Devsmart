"""
skill_prd_scan - Runner

扫描现有项目的目录结构、技术栈和代码依赖
"""

import os
import json
import yaml
import logging
from typing import Dict, Any, List
from pathlib import Path

logger = logging.getLogger(__name__)

IGNORE_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "env",
    ".idea", ".vscode", ".gitignore", "dist", "build", "target",
    "*.pyc", "*.pyo", ".DS_Store", "*.log", "*.tmp"
}


class ProjectScanRunner:
    """项目结构扫描 Skill Runner"""

    def __init__(self, project_dir: str):
        self.project_dir = Path(project_dir)

    async def run(self) -> Dict[str, Any]:
        try:
            if not self.project_dir.exists():
                return {
                    "status": "ERROR",
                    "message": f"项目目录不存在: {self.project_dir}"
                }

            project_structure = self._scan_directory(self.project_dir)
            tech_stack = self._detect_tech_stack()
            dependencies = self._extract_dependencies()
            existing_prd = self._find_existing_prd()

            return {
                "status": "SUCCESS",
                "message": "项目扫描完成",
                "project_structure": project_structure,
                "tech_stack": tech_stack,
                "dependencies": dependencies,
                "existing_prd": existing_prd
            }

        except Exception as e:
            logger.error(f"skill_prd_scan 执行失败: {e}")
            return {
                "status": "ERROR",
                "message": f"执行失败: {str(e)}"
            }

    def _scan_directory(self, directory: Path, depth: int = 3) -> Dict[str, Any]:
        if depth <= 0:
            return {}

        result = {}
        try:
            entries = sorted(directory.iterdir())
            for entry in entries:
                if self._should_ignore(entry):
                    continue

                if entry.is_dir():
                    result[entry.name] = self._scan_directory(entry, depth - 1)
                else:
                    result[entry.name] = {
                        "type": "file",
                        "size": entry.stat().st_size if entry.exists() else 0
                    }
        except PermissionError:
            pass

        return result

    def _should_ignore(self, path: Path) -> bool:
        name = path.name

        for pattern in IGNORE_DIRS:
            if pattern.startswith("*"):
                if name.endswith(pattern[1:]):
                    return True
            elif pattern.endswith("*"):
                if name.startswith(pattern[:-1]):
                    return True
            else:
                if name == pattern:
                    return True

        return False

    def _detect_tech_stack(self) -> Dict[str, Any]:
        tech_stack = {
            "backend": [],
            "frontend": [],
            "database": [],
            "devops": [],
            "other": []
        }

        files = list(self.project_dir.glob("**/*"))
        file_names = [f.name.lower() for f in files]

        for f in files:
            name = f.name.lower()
            path_str = str(f).lower()

            if name == "requirements.txt":
                tech_stack["backend"].append("Python")
            elif name == "pyproject.toml":
                tech_stack["backend"].append("Python (Poetry)")
            elif name == "go.mod":
                tech_stack["backend"].append("Go")
            elif name == "package.json":
                if "backend" not in path_str and "server" not in path_str:
                    tech_stack["frontend"].append("Node.js")
            elif name == "cargo.toml":
                tech_stack["backend"].append("Rust")
            elif name == "pom.xml":
                tech_stack["backend"].append("Java/Maven")
            elif name == "build.gradle":
                tech_stack["backend"].append("Java/Gradle")
            elif name.endswith(".rs"):
                tech_stack["backend"].append("Rust")
            elif name.endswith(".go"):
                tech_stack["backend"].append("Go")
            elif name.endswith(".py"):
                tech_stack["backend"].append("Python")

            if name == "dockerfile" or name == "docker-compose.yml":
                tech_stack["devops"].append("Docker")
            elif name == "kubernetes" or "k8s" in path_str:
                tech_stack["devops"].append("Kubernetes")

            if name == "main.ts" or name == "app.vue":
                tech_stack["frontend"].append("Vue.js")
            elif name == "main.tsx" or name == "app.tsx":
                tech_stack["frontend"].append("React")
            elif name == "angular.json":
                tech_stack["frontend"].append("Angular")

            if name == "docker-compose.yml":
                with open(f, 'r') as dc:
                    dc_content = dc.read().lower()
                    if "postgres" in dc_content:
                        tech_stack["database"].append("PostgreSQL")
                    elif "mysql" in dc_content:
                        tech_stack["database"].append("MySQL")
                    elif "mongodb" in dc_content:
                        tech_stack["database"].append("MongoDB")
                    elif "redis" in dc_content:
                        tech_stack["other"].append("Redis")

            if name.endswith(".sql"):
                tech_stack["database"].append("SQL Database")

        for key in tech_stack:
            tech_stack[key] = list(set(tech_stack[key]))

        return tech_stack

    def _extract_dependencies(self) -> Dict[str, Any]:
        dependencies = {}

        python_req = self.project_dir / "requirements.txt"
        if python_req.exists():
            with open(python_req, 'r') as f:
                dependencies["python"] = [line.strip() for line in f if line.strip() and not line.startswith("#")]

        pkg_json = self.project_dir / "package.json"
        if pkg_json.exists():
            with open(pkg_json, 'r') as f:
                pkg_data = json.load(f)
                dependencies["npm"] = pkg_data.get("dependencies", {})
                dependencies["npm_dev"] = pkg_data.get("devDependencies", {})

        go_mod = self.project_dir / "go.mod"
        if go_mod.exists():
            with open(go_mod, 'r') as f:
                go_deps = []
                for line in f:
                    if line.strip().startswith("require"):
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            go_deps.append(parts[1])
                dependencies["go"] = go_deps

        return dependencies

    def _find_existing_prd(self) -> Dict[str, Any]:
        prd_info = {
            "found": False,
            "versions": [],
            "latest_version": None,
            "files": []
        }

        docs_dir = self.project_dir / "docs"
        if docs_dir.exists():
            for f in docs_dir.glob("*prd*"):
                prd_info["found"] = True
                prd_info["files"].append(str(f.relative_to(self.project_dir)))

                if f.name.startswith("human_prd_v") or f.name.startswith("machine_prd_v"):
                    try:
                        version_str = f.stem.replace("human_prd_v", "").replace("machine_prd_v", "")
                        version = int(version_str)
                        if version not in prd_info["versions"]:
                            prd_info["versions"].append(version)
                    except ValueError:
                        continue

        if prd_info["versions"]:
            prd_info["latest_version"] = max(prd_info["versions"])
            latest_human = docs_dir / f"human_prd_v{prd_info['latest_version']}.md"
            latest_machine = docs_dir / f"machine_prd_v{prd_info['latest_version']}.yaml"

            if latest_human.exists():
                prd_info["latest_human_prd"] = str(latest_human.relative_to(self.project_dir))
            if latest_machine.exists():
                prd_info["latest_machine_prd"] = str(latest_machine.relative_to(self.project_dir))

        return prd_info