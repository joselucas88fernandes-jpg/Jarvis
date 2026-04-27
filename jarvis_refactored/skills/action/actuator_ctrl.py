from jarvis_refactored.interfaces import SkillInput, SkillOutput, SafetyResponse

def actuator_ctrl(skill_input: SkillInput) -> SkillOutput:
    logs = ["actuator_ctrl skill invoked"]
    actuator = skill_input.payload.get("actuator")
    position = skill_input.payload.get("position")

    # Mandatory Safety Check
    safety_context = skill_input.context.get("safety", {})
    if not isinstance(safety_context, SafetyResponse) or safety_context.decision != "PASS":
        return SkillOutput(
            task_id=skill_input.task_id,
            status="FAIL",
            result={"error": "Safety check not passed or missing."},
            logs=logs,
            metrics={},
        )

    try:
        command = f"{actuator.upper()}:{position}"
        logs.append(f"Generated command: {command}")

        return SkillOutput(
            task_id=skill_input.task_id,
            status="SUCCESS",
            result={"command": command},
            logs=logs,
            metrics={},
        )
    except Exception as e:
        return SkillOutput(
            task_id=skill_input.task_id,
            status="FAIL",
            result={"error": str(e)},
            logs=logs,
            metrics={},
        )
