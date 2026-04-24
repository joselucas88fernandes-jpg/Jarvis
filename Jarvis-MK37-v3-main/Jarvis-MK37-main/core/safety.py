
import ast
import logging

class SafetyInterlock:
    """
    A safety mechanism to prevent the agent from executing harmful code
    by performing an AST analysis.
    """

    def __init__(self):
        # Extend this list with any other dangerous patterns.
        self.disallowed_patterns = {
            ast.Call: [
                ("os.system",),
                ("subprocess.run", "rm -rf"),
                ("shutil.rmtree",)
            ],
            ast.Import: [
                ("os",),
                ("subprocess",),
                ("shutil",)
            ],
            ast.ImportFrom: [
                ("os",),
                ("subprocess",),
                ("shutil",)
            ]
        }
        # List of allowed built-in functions
        self.allowed_builtins = [
            'print', 'len', 'isinstance', 'str', 'int', 'float', 'list', 'dict', 'tuple', 'set', 
            'range', 'sum', 'min', 'max', 'abs', 'round', 'sorted', 'any', 'all', 'zip', 'enumerate',
            'bool'
        ]

    def verify_code(self, code_string: str) -> bool:
        """
        Verifies the code against a set of safety rules using AST analysis.
        """
        try:
            tree = ast.parse(code_string)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    # Check for disallowed function calls
                    for pattern in self.disallowed_patterns.get(ast.Call, []):
                        if self._is_call_match(node, pattern):
                            logging.warning(f"Disallowed call found: {ast.dump(node)}")
                            return False
                    # Check for use of disallowed built-in functions
                    if isinstance(node.func, ast.Name) and node.func.id not in self.allowed_builtins:
                        # Allow calls to user-defined functions
                        # This simple check can be improved with more context
                        pass

                # Check for disallowed imports
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    module_name = self._get_module_name(node)
                    if module_name in self.disallowed_patterns.get(type(node), []):
                        logging.warning(f"Disallowed import found: {module_name}")
                        return False

        except SyntaxError as e:
            logging.error(f"Syntax error in code: {e}")
            return False
        return True

    def _is_call_match(self, node: ast.Call, pattern: tuple) -> bool:
        """Check if a call node matches a disallowed pattern."""
        if len(pattern) == 1:
            if isinstance(node.func, ast.Attribute) and node.func.value.id == pattern[0].split('.')[0] and node.func.attr == pattern[0].split('.')[1]:
                return True
            if isinstance(node.func, ast.Name) and node.func.id == pattern[0]:
                return True
        elif len(pattern) > 1:
            # For calls like subprocess.run('rm -rf')
            if self._is_call_match(node, (pattern[0],)):
                for arg in node.args:
                    if isinstance(arg, ast.Str) and pattern[1] in arg.s:
                        return True
        return False

    def _get_module_name(self, node: ast.AST) -> str:
        """Get the module name from an import node."""
        if isinstance(node, ast.Import):
            return node.names[0].name
        if isinstance(node, ast.ImportFrom):
            return node.module
        return ""

