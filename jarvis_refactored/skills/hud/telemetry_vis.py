import time
from jarvis_refactored.interfaces import SkillInput, SkillOutput
from jarvis_refactored.core.db_manager import system_state

LAST_CALL_TIME = 0
REFRESH_RATE = 10  # 10Hz

def throttle_check() -> bool:
    global LAST_CALL_TIME
    current_time = time.time()
    if (current_time - LAST_CALL_TIME) < 1.0 / REFRESH_RATE:
        return False
    LAST_CALL_TIME = current_time
    return True

def telemetry_vis(skill_input: SkillInput) -> SkillOutput:
    if not throttle_check():
        return SkillOutput(
            task_id=skill_input.task_id,
            status="FAIL",
            result={"error": "Rate limit exceeded"},
            metrics={"latency": 0, "throttle_hit": True}, # Adicionado campo metrics
            logs=["Throttled to maintain 10Hz refresh rate."]
        )
    
    current_state = system_state.get_state()
    telemetry_package = {
        "hardware_status": current_state.get("hardware_status", {}),
        "active_tasks": current_state.get("active_tasks", []),
        "decision_trace": current_state.get("decision_trace", [])
    }
    
    return SkillOutput(
        task_id=skill_input.task_id,
        status="SUCCESS",
        result=telemetry_package,
        metrics={"latency": 0.001, "nodes_active": len(telemetry_package["hardware_status"])}, # Adicionado campo metrics
        logs=["Telemetry package prepared for HUD."],
    )
