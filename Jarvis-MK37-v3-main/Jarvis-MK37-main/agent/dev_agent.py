
import asyncio
import json
import logging
import tempfile
import unittest
from pathlib import Path
import os

import paramiko # For SSH connection
from git import Repo, diff

from core.llm_manager import LLMManager
from core.safety import SafetyInterlock

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DeveloperAgent:
    """
    A self-evolving agent that can inspect, analyze, and improve its own codebase.
    It uses a hybrid LLM strategy for robustness and can execute code in a distributed sandbox.
    """

    def __init__(self, project_root: str, llm_manager: LLMManager, ui=None, 
                 compiler_node_ip: str = None, compiler_node_user: str = None, compiler_node_key_path: str = None):
        self.project_root = Path(project_root)
        self.repo = Repo(self.project_root)
        self.llm_manager = llm_manager
        self.safety_interlock = SafetyInterlock()
        self.ui = ui

        self.compiler_node_ip = compiler_node_ip
        self.compiler_node_user = compiler_node_user
        self.compiler_node_key_path = compiler_node_key_path

    def log_to_ui(self, message: str):
        if self.ui:
            self.ui.write_log(message)
        else:
            logging.info(message)

    def self_inspect(self) -> dict:
        """
        Inspects the project directory and returns a tree structure.
        """
        file_tree = {}
        for root, dirs, files in os.walk(self.project_root):
            if '.git' in dirs:
                dirs.remove('.git')
            if '.idea' in dirs:
                dirs.remove('.idea')
            root_path = Path(root).relative_to(self.project_root)
            file_tree[str(root_path)] = {"directories": dirs, "files": files}
        return file_tree

    def _get_changed_snippets(self) -> str:
        """
        Gets the diff of the current changes to optimize context sent to the LLM.
        """
        diffs = self.repo.index.diff(None, create_patch=True)
        if not diffs:
            return "No current changes."
        
        return "\n".join([str(d) for d in diffs])

    async def analyze_codebase(self) -> dict:
        """
        Analyzes the codebase using the LLM manager, focusing on changed snippets.
        Identifies logic gaps, optimization opportunities, or new features.
        """
        self.log_to_ui("DEV: Starting codebase analysis...")
        file_tree = self.self_inspect()
        changed_snippets = self._get_changed_snippets()

        # Context Optimizer: Focus on changes and key files.
        analysis_prompt = f"""
        Analyze the following codebase of 'Project Jarvis' for self-improvement.
        File structure: {json.dumps(file_tree, indent=2)}

        Recent changes (diff):
        {changed_snippets}

        Based on the above, identify one of the following:
        1. A bug to fix.
        2. A feature to add.
        3. An optimization to implement.

        Return a JSON object with: `target_file`, `improvement_type` (bugfix/feature/optimization), and `logic_blueprint` (a detailed plan for the code).
        """

        response_text = await self.llm_manager.generate_content(analysis_prompt)
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            self.log_to_ui("DEV: Error decoding LLM analysis response.")
            return {}

    async def generate_code(self, logic_blueprint: str) -> tuple[str, str]:
        """
        Generates Python code and a corresponding test suite based on the logic blueprint.
        """
        self.log_to_ui("DEV: Generating new code and tests...")
        generation_prompt = f"""
        Based on this logic blueprint: '{logic_blueprint}',
        generate a Python code snippet and a pytest unit test for it.

        Return a JSON object with two keys: `code` and `test`.
        """

        response_text = await self.llm_manager.generate_content(generation_prompt)
        try:
            code_json = json.loads(response_text)
            new_code = code_json.get("code", "")
            test_code = code_json.get("test", "")
            return new_code, test_code
        except json.JSONDecodeError:
            self.log_to_ui("DEV: Error decoding LLM code generation response.")
            return "", ""

    async def create_sandbox(self, new_code: str, test_code: str, use_compiler_node: bool = False) -> bool:
        """
        Creates a sandbox environment to write and test new code, with an option
        to execute on a remote compiler node.
        """
        if not self.safety_interlock.verify_code(new_code) or not self.safety_interlock.verify_code(test_code):
            self.log_to_ui("DEV: New code failed safety interlock. Aborting sandbox.")
            return False

        if use_compiler_node and self.compiler_node_ip:
            return await self.create_remote_sandbox(new_code, test_code)
        else:
            return await self.create_local_sandbox(new_code, test_code)

    async def create_local_sandbox(self, new_code: str, test_code: str) -> bool:
        """
        Runs tests in a local temporary directory.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            new_module_path = temp_path / "new_module.py"
            test_module_path = temp_path / "test_suite.py"

            with open(new_module_path, "w") as f:
                f.write(new_code)
            with open(test_module_path, "w") as f:
                f.write(test_code)

            self.log_to_ui(f"DEV: Local sandbox created at {temp_dir}")
            return await self.run_tests_locally(test_module_path)

    async def run_tests_locally(self, test_path: Path) -> bool:
        """
        Runs pytest on the local machine.
        """
        process = await asyncio.create_subprocess_exec(
            "pytest", str(test_path),
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            self.log_to_ui("DEV: Local tests passed.")
            return True
        else:
            self.log_to_ui(f"DEV: Local tests failed. stdout: {stdout.decode()} stderr: {stderr.decode()}")
            return False

    async def create_remote_sandbox(self, new_code: str, test_code: str) -> bool:
        """
        Executes tests on a remote compiler node via SSH.
        """
        self.log_to_ui(f"DEV: Creating remote sandbox on {self.compiler_node_ip}")
        try:
            with paramiko.SSHClient() as ssh:
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(self.compiler_node_ip, username=self.compiler_node_user, key_filename=self.compiler_node_key_path)

                sftp = ssh.open_sftp()
                remote_temp_dir = sftp.normalize("jarvis_sandbox")
                sftp.mkdir(remote_temp_dir)
                
                with sftp.open(f"{remote_temp_dir}/new_module.py", "w") as f:
                    f.write(new_code)
                with sftp.open(f"{remote_temp_dir}/test_suite.py", "w") as f:
                    f.write(test_code)

                stdin, stdout, stderr = ssh.exec_command(f"pytest {remote_temp_dir}/test_suite.py")
                exit_status = stdout.channel.recv_exit_status()

                # Cleanup
                ssh.exec_command(f"rm -rf {remote_temp_dir}")

                if exit_status == 0:
                    self.log_to_ui("DEV: Remote tests passed.")
                    return True
                else:
                    self.log_to_ui(f"DEV: Remote tests failed. stdout: {stdout.read().decode()} stderr: {stderr.read().decode()}")
                    return False
        except Exception as e:
            self.log_to_ui(f"DEV: Remote sandbox execution failed. Error: {e}")
            return False

    def generate_proactive_report(self, analysis: dict, code_changes: str) -> str:
        """
        Generates a summary of the proposed changes for user approval.
        """
        return f"""
        System Update Report:

        - **Improvement Type:** {analysis.get('improvement_type')}
        - **Target File:** {analysis.get('target_file')}
        - **Summary:** {analysis.get('logic_blueprint')}
        - **Code Changes:**
        ```diff
        {code_changes}
        ```
        This update has been tested in a sandbox environment. Do you approve these changes?
        """
