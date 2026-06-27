import json

from app.models.state import CodeGuardState
from app.prompts.scanner_prompt import SCANNER_PROMPT
from app.tools.ast_tools import ASTTools
from app.tools.groq_tools import ask_groq
from app.tools.repo_tools import RepoTools


class RepositoryScannerAgent:
    role = "Hybrid repository intelligence agent"
    goal = "Map Python code deterministically, then use LLM reasoning to summarize architecture and scan strategy."
    tools = [
        "recursive Python file discovery",
        "Python AST parser",
        "symbol extractor",
        "Groq/LangChain repository reasoning model",
    ]

    def __call__(self, state: CodeGuardState):
        return self.run(state)

    def run(self, state: CodeGuardState):
        repo = state["repo_path"]
        python_files = RepoTools.find_python_files(repo)
        repository_map = {}
        skipped_files = []

        for file in python_files:
            try:
                tree = ASTTools.parse_python_file(file)
                repository_map[file] = ASTTools.extract_symbols(tree)
            except Exception as exc:
                skipped_files.append({
                    "file": file,
                    "reason": str(exc)
                })

        scanner_intelligence = self.analyze_repository(
            state,
            python_files,
            repository_map,
            skipped_files
        )

        return {
            "python_files": python_files,
            "repository_map": repository_map,
            "scanner_intelligence": scanner_intelligence,
            "agent_reports": [
                *state.get("agent_reports", []),
                {
                    "agent": "scanner",
                    "role": self.role,
                    "goal": self.goal,
                    "tools": self.tools,
                    "summary": scanner_intelligence.get(
                        "architecture_summary",
                        self.build_summary(python_files, repository_map, skipped_files)
                    ),
                    "skipped_files": skipped_files,
                    "intelligence": scanner_intelligence,
                }
            ]
        }

    def analyze_repository(self, state, python_files, repository_map, skipped_files):
        fallback = self.build_fallback_intelligence(python_files, repository_map, skipped_files)
        repository_summary = self.build_repository_summary(repository_map)

        prompt = SCANNER_PROMPT.format(
            bug_report=state.get("bug_report", ""),
            error_log=state.get("error_log", ""),
            repository_summary=repository_summary
        )

        intelligence = ask_groq(prompt, fallback=fallback)

        if not isinstance(intelligence, dict):
            return fallback

        return {
            "architecture_summary": intelligence.get("architecture_summary") or fallback["architecture_summary"],
            "detected_frameworks": self.as_list(intelligence.get("detected_frameworks")) or fallback["detected_frameworks"],
            "entrypoints": self.as_list(intelligence.get("entrypoints")) or fallback["entrypoints"],
            "important_modules": self.as_list(intelligence.get("important_modules")) or fallback["important_modules"],
            "risk_areas": self.as_list(intelligence.get("risk_areas")) or fallback["risk_areas"],
            "scan_strategy": intelligence.get("scan_strategy") or fallback["scan_strategy"],
        }

    def build_summary(self, python_files, repository_map, skipped_files):
        function_count = sum(len(data["functions"]) for data in repository_map.values())
        class_count = sum(len(data["classes"]) for data in repository_map.values())

        return (
            f"Mapped {len(python_files)} Python files, "
            f"{function_count} functions, and {class_count} classes. "
            f"Skipped {len(skipped_files)} files."
        )

    def build_repository_summary(self, repository_map):
        entries = []

        for file_name, details in list(repository_map.items())[:80]:
            functions = [function["name"] for function in details.get("functions", [])[:12]]
            classes = [class_data["name"] for class_data in details.get("classes", [])[:8]]
            imports = details.get("imports", [])[:12]

            entries.append({
                "file": file_name,
                "functions": functions,
                "classes": classes,
                "imports": imports,
            })

        return json.dumps(entries, indent=2)[:14000]

    def build_fallback_intelligence(self, python_files, repository_map, skipped_files):
        frameworks = self.detect_frameworks(repository_map)
        entrypoints = self.detect_entrypoints(repository_map)

        return {
            "architecture_summary": self.build_summary(python_files, repository_map, skipped_files),
            "detected_frameworks": frameworks or ["Unknown"],
            "entrypoints": entrypoints,
            "important_modules": list(repository_map.keys())[:8],
            "risk_areas": [
                "Functions with external imports, request handlers, persistence logic, or complex branching should be reviewed first."
            ],
            "scan_strategy": "Use AST symbols to identify entrypoints and pass likely modules to the Bug Hunter Agent.",
        }

    def detect_frameworks(self, repository_map):
        imports = {
            imported
            for details in repository_map.values()
            for imported in details.get("imports", [])
        }

        frameworks = []

        if any(imported.startswith("fastapi") for imported in imports):
            frameworks.append("FastAPI")

        if any(imported.startswith("flask") for imported in imports):
            frameworks.append("Flask")

        if any(imported.startswith("django") for imported in imports):
            frameworks.append("Django")

        if any(imported.startswith("pytest") for imported in imports):
            frameworks.append("Pytest")

        return frameworks

    def detect_entrypoints(self, repository_map):
        entrypoints = []

        for file_name, details in repository_map.items():
            lower_name = file_name.lower().replace("\\", "/")

            if lower_name.endswith(("main.py", "app.py", "server.py")):
                entrypoints.append(file_name)
                continue

            imports = details.get("imports", [])

            if "fastapi" in imports or "flask" in imports:
                entrypoints.append(file_name)

        return entrypoints[:8]

    def as_list(self, value):
        if isinstance(value, list):
            return [str(item) for item in value if item]

        if isinstance(value, str) and value.strip():
            return [value.strip()]

        return []


scanner = RepositoryScannerAgent()


def scanner_agent(state: CodeGuardState):
    return scanner(state)
