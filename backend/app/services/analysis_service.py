from app.orchestrator.graph import codeguard_graph
from app.tools.zip_tools import ZipTools


class AnalysisService:

    @staticmethod
    def analyze(zip_bytes, bug_report, error_log):

        # Extract uploaded repository
        temp_dir, repo_path = ZipTools.extract_repository(zip_bytes)

        try:

            # Initial LangGraph state
            state = {
                "repo_path": str(repo_path),
                "bug_report": bug_report,
                "error_log": error_log,
                "python_files": [],
                "repository_map": {},
                "suspects": [],
                "diagnosis": {},
                "generated_tests": [],
                "final_report": {}
            }

            # Run LangGraph workflow
            result = codeguard_graph.invoke(state)

            # Build repository summary
            repository = result["repository_map"]

            function_count = 0
            class_count = 0

            for file_data in repository.values():
                function_count += len(file_data["functions"])
                class_count += len(file_data["classes"])

            # Return only the data the frontend needs
            return {
                "summary": {
                    "python_files": len(result["python_files"]),
                    "functions": function_count,
                    "classes": class_count
                },
                "suspects": result["suspects"],
                "diagnosis": result["diagnosis"]
            }

        finally:
            # Always clean temporary files
            ZipTools.cleanup(temp_dir)