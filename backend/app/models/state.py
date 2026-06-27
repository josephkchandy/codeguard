from typing import TypedDict, Dict, List, Any


class CodeGuardState(TypedDict):

    repo_path: str

    bug_report: str

    error_log: str

    python_files: List[str]

    repository_map: Dict[str, Any]

    scanner_intelligence: Dict[str, Any]

    suspects: List[Dict[str, Any]]

    diagnosis: Dict[str, Any]

    agent_reports: List[Dict[str, Any]]

    generated_tests: List[str]

    final_report: Dict[str, Any]
