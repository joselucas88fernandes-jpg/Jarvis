
import ast
import logging
import re

class SafetyInterlock:
    """
    A multi-layer safety mechanism to prevent the agent from executing harmful code.
    Combines AST analysis, semantic regex checks, and hardware state simulation.
    """

    def __init__(self, ui=None):
        self.ui = ui
        # --- Dynamic Payload & Obfuscation Patterns ---
        self.disallowed_functions = {'eval', 'exec', 'getattr', 'setattr', '__import__'}

        # --- Hardware State Simulation Patterns ---
        self.hardware_danger_patterns = {
            "Resonance Risk (High-Frequency Loop)": r"while\s*\(.*\)\s*\{[^\}]*?delay\s*\(\s*([0-9]|[1-4][0-9])\s*\);[^\}]*?\}",
            "Sustained 100% PWM (Thermal Risk)": r"analogWrite\s*\(\s*\d+\s*,\s*255\s*\);(?<!.*#SAFETY_OVERRIDE:\s*SUSTAINED_PWM_OK.*)",
            "Invalid Baud Rate (Buffer Desync Risk)": r"Serial\.begin\s*\(\s*(?!(9600|115200))\d+\s*\);",
        }

    def _verify_ast(self, code_string: str) -> bool:
        """Verifies against dangerous function calls using AST analysis."""
        try:
            tree = ast.parse(code_string)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    if node.func.id in self.disallowed_functions:
                        self._log(f"AST Alert: Disallowed function '{node.func.id}' found.", "error")
                        return False
        except SyntaxError as e:
            self._log(f"AST Syntax error in code: {e}", "error")
            return False
        return True

    def _verify_hardware_semantics(self, code_string: str) -> bool:
        """Performs hardware-specific semantic checks using regex."""
        for threat, pattern in self.hardware_danger_patterns.items():
            # Use re.DOTALL to make `.` match newlines for multi-line checks
            if re.search(pattern, code_string, re.DOTALL):
                self._log(f"Hardware Safety Alert: '{threat}' detected.", "error")
                return False
        return True

    def verify_code(self, code_string: str) -> bool:
        """Runs a comprehensive verification suite."""
        self._log("SYS: Running comprehensive safety scan...", "info")
        if not self._verify_ast(code_string):
            return False
        if not self._verify_hardware_semantics(code_string):
            return False
        self._log("SYS: Safety scan passed.", "info")
        return True

    def _log(self, message: str, level: str):
        logging.info(message) # Default logging
        if self.ui:
            # In the future, this could send a message to the UI
            pass
