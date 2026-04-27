from jarvis_refactored.interfaces import SkillInput, SkillOutput
from jarvis_refactored.skills.registry import skill_registry

def task_decomp(skill_input: SkillInput) -> SkillOutput:
    goal = skill_input.payload.get("goal", "")
    logs = [f"Decomposing goal: {goal}"]

    # Mock LLM logic
    available_skills = skill_registry.list_skills()
    # In a real system, an LLM would map the goal to these skills.
    # For now, we use simple keyword matching.
    steps = []
    if "calibrate" in goal and "servos" in goal:
        steps.append({"skill": "actuator_ctrl", "params": {"actuator": "ALL_SERVOS", "position": 0}})
        steps.append({"skill": "sensor_read", "params": {"raw_data": "STATUS:CALIBRATED"}})

    return SkillOutput(
        task_id=skill_input.task_id,
        status="SUCCESS",
        result={"steps": steps},
        logs=logs,
    )
