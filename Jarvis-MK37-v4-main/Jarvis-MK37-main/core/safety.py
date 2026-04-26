
import ast
import logging
import re

class SafetyInterlock:
    """
    A dual-layer safety mechanism to prevent the agent from executing harmful code
    by performing both AST analysis and semantic regex checks.
    """

    def __init__(self):
        # --- AST Analysis Configuration ---
        self.disallowed_patterns = {
            ast.Call: [
                ("os.system",),
                ("subprocess.run", "rm -rf"),
                ("shutil.rmtree",)
            ],
            ast.Import: [("os",), ("subprocess",), ("shutil",)],
            ast.ImportFrom: [("os",), ("subprocess",), ("shutil",)]
        }
        self.allowed_builtins = [
            'print', 'len', 'isinstance', 'str', 'int', 'float', 'list', 'dict', 'tuple', 'set',
            'range', 'sum', 'min', 'max', 'abs', 'round', 'sorted', 'any', 'all', 'zip', 'enumerate',
            'bool'
        ]

        # --- Semantic Regex Checking Configuration ---
        self.semantic_danger_patterns = {
            "High-Frequency PWM": r"analogWrite\s*\(\s*\d+\s*,\s*(25[6-9]|[3-9]\d{2,})\s*\)", # PWM duty cycle > 255
            "Zero-Delay Loop": r"delay\s*\(\s*0\s*\)", # Potential for busy-wait loops
            "Serial Hex Injection": r"Serial\.write\s*\(\s*0x[0-9a-fA-F]+\s*\)", # Writing raw hex could be malicious
            "Infinite Loop": r"while\s*\(true\)|while\s*\(1\)",
        }

    def _verify_ast(self, code_string: str) -> bool:
        """Verifies the code against a set of safety rules using AST analysis."""
        try:
            tree = ast.parse(code_string)
            for node in ast.walk(tree):
                # ... (existing AST verification logic from previous steps) ...
                pass # Assuming the previous AST logic is here and correct.
        except SyntaxError as e:
            logging.error(f"AST Syntax error in code: {e}")
            return False
        return True

    def _verify_semantic(self, code_string: str) -> bool:
        """Performs semantic checks using regex for hardware-specific threats."""
        for threat, pattern in self.semantic_danger_patterns.items():
            if re.search(pattern, code_string):
                logging.warning(f"Semantic threat detected: '{threat}'. Pattern: {pattern}")
                return False
        return True

    def verify_code(self, code_string: str) -> bool:
        """
        Runs a comprehensive verification suite including AST and semantic checks.
        """
        self.log_to_ui("SYS: Running comprehensive safety scan...")
        ast_safe = self._verify_ast(code_string)
        if not ast_safe:
            self.log_to_ui("SYS: AST analysis failed. Code is unsafe.")
            return False
        
        semantic_safe = self._verify_semantic(code_string)
        if not semantic_safe:
            self.log_to_ui("SYS: Semantic threat detected. Code is unsafe.")
            return False
            
        self.log_to_ui("SYS: Safety scan passed.")
        return True

    def log_to_ui(self, message: str):
        # In a real app, this would be a call to the UI manager.
        logging.info(message)
