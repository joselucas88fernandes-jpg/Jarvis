from jarvis_refactored.interfaces import SkillInput, SkillOutput

def sensor_read(skill_input: SkillInput) -> SkillOutput:
    logs = ["sensor_read skill invoked"]
    raw_data = skill_input.payload.get("raw_data", "")
    metrics = {"parsed_data_points": 0}

    try:
        # Example: "TEMP:25.5,VOLT:12.1"
        telemetry = {}
        for item in raw_data.split(","):
            key, value = item.split(":")
            telemetry[key] = float(value)
            metrics["parsed_data_points"] += 1

        logs.append(f"Parsed telemetry: {telemetry}")

        return SkillOutput(
            task_id=skill_input.task_id,
            status="SUCCESS",
            result={"telemetry": telemetry},
            logs=logs,
            metrics=metrics,
        )
    except Exception as e:
        return SkillOutput(
            task_id=skill_input.task_id,
            status="FAIL",
            result={"error": str(e)},
            logs=logs,
            metrics=metrics,
        )
