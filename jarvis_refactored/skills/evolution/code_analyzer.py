from jarvis_refactored.interfaces import SkillInput, SkillOutput
import subprocess

def code_analyzer(skill_input: SkillInput) -> SkillOutput:
    file_path = skill_input.payload.get("file_path", "")
    logs = [f"Analyzing file: {file_path}"]

    try:
        # Mock LLM analysis using a simple linter like flake8
        result = subprocess.run(["flake8", file_path], capture_output=True, text=True)
        findings = []
        for line in result.stdout.splitlines():
            findings.append({"description": line, "severity": "LOW"})

        return SkillOutput(
            task_id=skill_input.task_id,
            status="SUCCESS",
            result={"findings": findings},
            logs=logs,
        )
    except FileNotFoundError:
        # Handle case where flake8 is not installed
        logs.append("flake8 not found, using basic analysis.")
        # Basic analysis for demonstration
        with open(file_path, 'r') as f:
            lines = f.readlines()
            if len(lines) > 100:
                return SkillOutput(
                    task_id=skill_input.task_id,
                    status="SUCCESS",
                    result={"findings": [{"description": "File is longer than 100 lines.", "severity": "MEDIUM"}]},
                    logs=logs,
                )
            else:
                return SkillOutput(
                    task_id=skill_input.task_id,
                    status="SUCCESS",
                    result={"findings": []},
                    logs=logs,
                )
    except Exception as e:
        return SkillOutput(
            task_id=skill_input.task_id,
            status="FAIL",
            result={"error": str(e)},
            logs=logs,
        )
