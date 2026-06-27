# Repository utilities
from pathlib import Path


class RepoTools:

    @staticmethod
    def find_python_files(repo_path: str):

        python_files = []

        repo = Path(repo_path)

        for file in repo.rglob("*.py"):

            if "__pycache__" in str(file):
                continue

            python_files.append(str(file))

        return sorted(python_files)