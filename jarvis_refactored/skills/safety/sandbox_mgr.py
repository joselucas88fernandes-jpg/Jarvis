from jarvis_refactored.interfaces import SkillInput, SkillOutput
import subprocess
import sys
import threading


def trace_function(frame, event, arg):
    # A simple trace function to detect long-running code
    if event == 'line':
        # This is a very basic example. A real implementation would need
        # to be more sophisticated to avoid performance overhead.
        pass
    return trace_function

def sandbox_mgr(skill_input: SkillInput) -> SkillOutput:
    code_to_execute = skill_input.payload.get("code", "")
    logs = ["Executing code in sandbox"]

    def target():
        try:
            # A more secure sandbox would use a separate process with restricted permissions
            exec(code_to_execute, {'__builtins__': {}})
        except Exception as e:
            # This is a simple way to catch exceptions. A real sandbox would need
            # to handle stdout/stderr and resource limits.
            print(f"Sandbox execution error: {e}")

    # Using threading for a simple timeout mechanism
    thread = threading.Thread(target=target)
    thread.start()
    thread.join(timeout=5)  # 5-second timeout

    if thread.is_alive():
        # This is not a foolproof way to stop the thread, but it's a start
        logs.append("Code execution timed out")
        return SkillOutput(
            task_id=skill_input.task_id,
            status="FAIL",
            result={"error": "Execution timed out"},
            logs=logs,
        )

    return SkillOutput(
        task_id=skill_input.task_id,
        status="SUCCESS",
        result={"output": "Execution completed"},
        logs=logs,
    )
