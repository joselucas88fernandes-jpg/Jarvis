
import logging

class SafetyInterlock:
    """
    A safety mechanism to prevent the agent from executing harmful code.
    """

    def __init__(self):
        # In a real implementation, this would involve a more sophisticated
        # set of rules and possibly an LLM to evaluate code for safety.
        self.disallowed_operations = [
            "os.system",
            "subprocess.run('rm -rf')", # A classic example of what to avoid
            "shutil.rmtree"
        ]

    def verify_code(self, code_string: str) -> bool:
        """
        Verifies the code against a set of safety rules.
        """
        for operation in self.disallowed_operations:
            if operation in code_string:
                logging.warning(f"Disallowed operation found in code: {operation}")
                return False
        return True
