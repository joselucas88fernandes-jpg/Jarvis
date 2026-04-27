from jarvis_refactored.interfaces import SkillInput, SkillOutput
from difflib import SequenceMatcher

def refactor_suggest(skill_input: SkillInput) -> SkillOutput:
    original_code = skill_input.payload.get("original_code", "")
    findings = skill_input.payload.get("findings", [])
    logs = ["Generating refactoring suggestions"]

    # Mock LLM logic for refactoring
    refactored_code = original_code
    for finding in findings:
        if "long" in finding["description"]:
            refactored_code = "# Refactored to be shorter\n" + original_code

    # Entropy Check
    similarity = SequenceMatcher(None, original_code, refactored_code).ratio()
    if similarity > 0.95 and skill_input.context.get("previous_attempt_failed", False):
        return SkillOutput(
            task_id=skill_input.task_id,
            status="FAIL",
            result={"error": "STOCHASTIC_LOOP detected"},
            logs=logs,
        )

    return SkillOutput(
        task_id=skill_input.task_id,
        status="SUCCESS",
        result={"refactored_code": refactored_code},
        logs=logs,
    )
