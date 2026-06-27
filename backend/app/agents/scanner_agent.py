from app.models.state import CodeGuardState
from app.tools.ast_tools import ASTTools
from app.tools.repo_tools import RepoTools


class RepositoryScannerAgent:
    role = "Deterministic repository mapping agent"
    goal = "Discover Python files and build structured code evidence for later agents."
    tools = [
        "recursive Python file discovery",
        "Python AST parser",
        "symbol extractor",
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

        return {
            "python_files": python_files,
            "repository_map": repository_map,
            "agent_reports": [
                *state.get("agent_reports", []),
                {
                    "agent": "scanner",
                    "role": self.role,
                    "goal": self.goal,
                    "tools": self.tools,
                    "summary": self.build_summary(python_files, repository_map, skipped_files),
                    "skipped_files": skipped_files,
                }
            ]
        }

    def build_summary(self, python_files, repository_map, skipped_files):
        function_count = sum(len(data["functions"]) for data in repository_map.values())
        class_count = sum(len(data["classes"]) for data in repository_map.values())

        return (
            f"Mapped {len(python_files)} Python files, "
            f"{function_count} functions, and {class_count} classes. "
            f"Skipped {len(skipped_files)} files."
        )


scanner = RepositoryScannerAgent()


def scanner_agent(state: CodeGuardState):
    return scanner(state)
