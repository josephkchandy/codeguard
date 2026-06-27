# Repository Scanner Agent
from app.models.state import CodeGuardState

from app.tools.repo_tools import RepoTools
from app.tools.ast_tools import ASTTools


def scanner_agent(state: CodeGuardState):

    repo = state["repo_path"]

    python_files = RepoTools.find_python_files(repo)

    repository_map = {}

    for file in python_files:

        try:

            tree = ASTTools.parse_python_file(file)

            repository_map[file] = ASTTools.extract_symbols(tree)

        except Exception:

            continue

    return {

        "python_files": python_files,

        "repository_map": repository_map

    }