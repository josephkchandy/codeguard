# AST parsing utilities
import ast


class ASTTools:

    @staticmethod
    def parse_python_file(file_path: str):

        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source)

        return tree

    @staticmethod
    def extract_symbols(tree):

        functions = []
        classes = []
        imports = []

        for node in ast.walk(tree):

            if isinstance(node, ast.FunctionDef):

                functions.append({
                    "name": node.name,
                    "line": node.lineno,
                    "docstring": ast.get_docstring(node)
                })

            elif isinstance(node, ast.ClassDef):

                methods = []

                for child in node.body:

                    if isinstance(child, ast.FunctionDef):

                        methods.append(child.name)

                classes.append({
                    "name": node.name,
                    "line": node.lineno,
                    "methods": methods
                })

            elif isinstance(node, ast.Import):

                for alias in node.names:

                    imports.append(alias.name)

            elif isinstance(node, ast.ImportFrom):

                if node.module:

                    imports.append(node.module)

        return {
            "functions": functions,
            "classes": classes,
            "imports": imports
        }