
import asyncio
import json
import logging
import os
from pathlib import Path

from core.llm_manager import LLMManager
from core.safety import SafetyInterlock

FAILURE_MANIFEST_PATH = "logs/failure_manifest.json"
SANDBOX_TIMEOUT = 120  # seconds

class DeveloperAgent:
    
    def __init__(self, project_root: str, llm_manager: LLMManager, ui=None):
        self.project_root = Path(project_root)
        self.llm_manager = llm_manager
        self.safety_interlock = SafetyInterlock()
        self.ui = ui
        self.failure_manifest = self._load_failure_manifest()

    def _load_failure_manifest(self) -> list:
        if os.path.exists(FAILURE_MANIFEST_PATH):
            with open(FAILURE_MANIFEST_PATH, 'r') as f:
                return json.load(f)
        return []

    def _update_failure_manifest(self, blueprint: str):
        self.failure_manifest.append({"failed_blueprint": blueprint, "timestamp": asyncio.get_event_loop().time()})
        os.makedirs(os.path.dirname(FAILURE_MANIFEST_PATH), exist_ok=True)
        with open(FAILURE_MANIFEST_PATH, 'w') as f:
            json.dump(self.failure_manifest, f, indent=2)

    async def analyze_codebase(self) -> dict:
        # ... (previous analysis logic)
        # Add context from the failure manifest to the prompt
        analysis_prompt = f"""
        Analyze the codebase for self-improvement.
        Avoid proposals similar to these previously failed blueprints: {json.dumps(self.failure_manifest[-5:], indent=2)}
        
        ... (rest of the prompt)
        """
        # ... (LLM call)
        return {}

    async def generate_code(self, logic_blueprint: str) -> tuple[str, str]:
        # Check if this blueprint has failed before
        if any(item['failed_blueprint'] == logic_blueprint for item in self.failure_manifest):
            self.log_to_ui("DEV: This logic blueprint has failed before. Aborting generation.")
            return "", ""
        # ... (rest of generation logic)
        return "", ""

    async def create_sandbox(self, new_code: str, test_code: str) -> bool:
        if not self.safety_interlock.verify_code(new_code) or not self.safety_interlock.verify_code(test_code):
            self.log_to_ui("DEV: New code failed safety interlock. Aborting sandbox.")
            return False

        with tempfile.TemporaryDirectory() as temp_dir:
            # ... (file writing logic) ...
            return await self.run_tests_in_sandbox(temp_dir)

    async def run_tests_in_sandbox(self, sandbox_dir: str) -> bool:
        """
        Runs pytest in a secure, resource-capped sandbox using subprocess.shell.
        """
        command = f"cd {sandbox_dir} && pytest"
        self.log_to_ui(f"DEV: Executing sandbox command: {command}")
        try:
            proc = await asyncio.wait_for(
                asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    limit=1024 * 1024 * 5,  # 5MB memory limit
                ),
                timeout=SANDBOX_TIMEOUT
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode == 0:
                self.log_to_ui("DEV: Sandbox tests passed.")
                return True
            else:
                self.log_to_ui(f"DEV: Sandbox tests failed. stderr: {stderr.decode()}")
                # Add the failing blueprint to the manifest
                # This requires getting the blueprint that led to this test
                # self._update_failure_manifest(logic_blueprint)
                return False
        except asyncio.TimeoutError:
            self.log_to_ui("DEV: Sandbox execution timed out.")
            # self._update_failure_manifest(logic_blueprint)
            return False
        except Exception as e:
            self.log_to_ui(f"DEV: Sandbox execution failed with an error: {e}")
            # self._update_failure_manifest(logic_blueprint)
            return False

    def log_to_ui(self, message: str):
        logging.info(message)

