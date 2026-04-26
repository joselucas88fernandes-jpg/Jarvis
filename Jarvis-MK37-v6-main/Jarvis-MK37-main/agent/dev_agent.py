
import asyncio
import logging
from pathlib import Path
import Levenshtein # Required: pip install python-Levenshtein

from core.llm_manager import LLMManager
from core.safety import SafetyInterlock
from core.db_manager import DatabaseManager

SIMILARITY_THRESHOLD = 0.90 # 90% similarity
MAX_RECURSION_DEPTH = 5

class DeveloperAgent:
    
    def __init__(self, project_root: str, llm_manager: LLMManager, db_manager: DatabaseManager, ui=None):
        self.project_root = Path(project_root)
        self.llm_manager = llm_manager
        self.safety_interlock = SafetyInterlock(ui=ui)
        self.db = db_manager
        self.ui = ui

    async def autonomous_loop(self):
        """The main autonomous loop for self-improvement."""
        # This would be triggered by a higher-level goal
        goal = "Refactor the codebase to improve performance."
        task_id = await self.db.create_task(goal)
        await self.execute_task(task_id, goal)

    async def execute_task(self, task_id: int, goal: str, recursion_depth=0):
        if recursion_depth >= MAX_RECURSION_DEPTH:
            self._log(f"Task {task_id}: Max recursion depth reached. Halting.", "error")
            await self.db.update_task_status(task_id, "HUMAN_INTERVENTION_REQUIRED")
            return

        self._log(f"Task {task_id}: Starting execution. Goal: {goal}", "info")
        
        # 1. Create Blueprint
        blueprint = await self.create_blueprint(task_id, goal)
        if not blueprint:
            return

        # 2. Generate Code
        code, test_code = await self.generate_code(task_id, blueprint)
        if not code:
            return

        # 3. Sandbox Execution
        test_passed = await self.run_in_sandbox(task_id, code, test_code)
        if test_passed:
            await self.db.update_task_status(task_id, "SUCCESS")
            self._log(f"Task {task_id}: Successfully completed.", "info")
            # ... (Code integration logic would go here)
        else:
            self._log(f"Task {task_id}: Tests failed. Re-evaluating strategy.", "warning")
            # Recursive call to try again with the same goal but new context
            await self.execute_task(task_id, goal, recursion_depth + 1)

    async def create_blueprint(self, task_id, goal):
        # In a real scenario, this would involve codebase analysis
        prompt = f"Create a technical blueprint to achieve the goal: {goal}"
        blueprint = await self.llm_manager.generate_text(prompt)
        await self.db.log_step(task_id, 'BLUEPRINT', content=blueprint)
        return blueprint

    async def generate_code(self, task_id: int, blueprint: str):
        prompt = f"Generate Python code and pytest tests based on this blueprint: {blueprint}"
        generated_code = await self.llm_manager.generate_text(prompt)

        # Mission 1: Entropy Circuit Breaker
        is_novel = await self.check_code_novelty(task_id, generated_code)
        if not is_novel:
            return "", ""

        if not self.safety_interlock.verify_code(generated_code):
            await self.db.log_step(task_id, 'GENERATE_CODE', content=generated_code, result='FAIL')
            await self.db.update_task_status(task_id, "FAILED_SAFETY_CHECK")
            return "", ""

        # Assume code and tests are parsed from generated_code
        code = "#...code..."
        test_code = "#...tests..."
        return code, test_code

    async def check_code_novelty(self, task_id: int, new_code: str) -> bool:
        """Checks if the new code is too similar to previous failures."""
        previous_failures = await self.db.get_recent_failures_for_task(task_id, limit=3)
        for failure in previous_failures:
            failed_code = failure['content']
            # Levenshtein.ratio gives similarity from 0.0 to 1.0
            similarity = Levenshtein.ratio(new_code, failed_code)
            
            if similarity > SIMILARITY_THRESHOLD:
                error_msg = f"Entropy Check Failed: Code is {similarity:.2%} similar to a previous failure."
                self._log(error_msg, "error")
                await self.db.log_step(task_id, 'STOCHASTIC_LOOP_DETECTED', content=error_msg)
                await self.db.update_task_status(task_id, "HUMAN_INTERVENTION_REQUIRED")
                return False
        return True

    async def run_in_sandbox(self, task_id, code, test_code) -> bool:
        # Mocked for now. This would use the asyncio.create_subprocess_shell from before.
        self._log(f"Task {task_id}: Running tests in sandbox...", "info")
        test_passed = True # Mock result
        result = 'PASS' if test_passed else 'FAIL'
        await self.db.log_step(task_id, 'SANDBOX_TEST', content=f"{code}\n---\n{test_code}", result=result)
        return test_passed

    async def resume_task(self, task: dict):
        """Resumes an unfinished task from the last successful checkpoint."""
        task_id = task['id']
        goal = task['goal']
        self._log(f"Resuming task {task_id}...", "info")
        # The execute_task loop is now stateful via the DB, so we can just re-trigger it.
        await self.execute_task(task_id, goal)

    def _log(self, message: str, level: str):
        logging.info(message)

