from jarvis_refactored.interfaces import SafetyResponse

async def analyze_intent(goal: str, payload: dict) -> SafetyResponse:
    """
    Analyzes the semantic intent of a task goal using mock logic.
    In a real system, this would involve a call to an LLM.
    """
    # Mock analysis: block any task with "critical" in the goal.
    if "critical" in goal.lower():
        return SafetyResponse(
            decision="BLOCK",
            reason="Goal involves a potentially critical operation.",
            risk_level=8,
        )

    # Mock analysis: require simulation for file operations.
    if "file" in payload.get("command", ""):
        return SafetyResponse(
            decision="REQUIRE_SIMULATION",
            reason="Task involves file system operations.",
            risk_level=5,
        )

    return SafetyResponse(
        decision="PASS",
        reason="Intent appears safe.",
        risk_level=1,
    )
