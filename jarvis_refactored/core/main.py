from fastapi import FastAPI
from pydantic import BaseModel
from jarvis_refactored.agent.task_manager import task_manager

app = FastAPI()

class TaskRequest(BaseModel):
    goal: str
    priority: int = 1

@app.post("/v1/tasks")
async def create_task(request: TaskRequest):
    task = await task_manager.execute_task(request.goal, request.priority)
    return {"task_id": task.id, "status": task.state}
