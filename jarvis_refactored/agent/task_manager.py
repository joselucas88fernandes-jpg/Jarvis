import asyncio
from typing import Dict, Any, List
from uuid import uuid4
from jarvis_refactored.interfaces import Task, SkillInput, SkillOutput
from jarvis_refactored.skills.registry import skill_registry
from jarvis_refactored.core.db_manager import system_state
from jarvis_refactored.skills.model.task_decomp import task_decomp


class TaskManager:
    def __init__(self):
        self._locks: Dict[str, asyncio.Lock] = {}

    async def execute_task(self, goal: str, priority: int) -> Task:
        task_id = str(uuid4())
        task = Task(id=task_id, goal=goal, priority=priority, steps=[], state="PENDING")
        system_state.update_state("active_tasks", task.dict())

        try:
            task.state = "RUNNING"

            # 1. Decompose task
            decomp_input = SkillInput(task_id=task_id, payload={"goal": goal})
            decomp_output = task_decomp(decomp_input)
            if decomp_output.status != "SUCCESS":
                raise Exception("Task decomposition failed")
            
            steps = decomp_output.result["steps"]
            system_state.update_state("decision_trace", {"task_id": task_id, "decision": "decomposed task", "steps": steps})
            task.steps.append(f"task_decomp: {steps}")

            # 2. Execute steps
            for step in steps:
                skill_name = step.get("skill")
                skill_params = step.get("params", {})
                domain, skill_func_name = skill_name.split("_", 1)
                skill = skill_registry.get_skill(domain, skill_func_name)

                if not skill:
                    raise ValueError(f"Skill {skill_name} not found.")

                skill_input = SkillInput(
                    task_id=task_id,
                    timestamp=asyncio.get_event_loop().time(),
                    source=self.__class__.__name__,
                    payload=skill_params,
                    context={}
                )

                # Execute skill and handle output
                skill_output = await skill(skill_input) if asyncio.iscoroutinefunction(skill) else skill(skill_input)

                if skill_output.status != "SUCCESS":
                    raise Exception(f"Skill {skill_name} failed: {skill_output.logs}")
                
                task.steps.append(f"{skill_name}: {skill_output.result}")

            task.state = "COMPLETED"

        except Exception as e:
            task.state = "FAILED"
            print(f"Task {task_id} failed: {e}")
        finally:
            system_state.update_state("active_tasks", task.dict())

        return task

task_manager = TaskManager()
