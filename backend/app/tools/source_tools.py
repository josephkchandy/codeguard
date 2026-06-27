import ast


class SourceTools:

    @staticmethod
    def extract_function_source(file_path: str, function_name: str, line_number: int):
        try:
            with open(file_path, "r", encoding="utf-8") as source_file:
                source = source_file.read()

            tree = ast.parse(source)

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.name == function_name and node.lineno == line_number:
                        return ast.get_source_segment(source, node)

            return SourceTools.extract_near_line(source, line_number)

        except Exception:
            return ""

    @staticmethod
    def extract_near_line(source: str, line_number: int, before: int = 6, after: int = 24):
        lines = source.splitlines()
        start = max(line_number - before, 0)
        end = min(line_number + after, len(lines))
        return "\n".join(lines[start:end])
