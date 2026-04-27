from pydantic import BaseModel, Field
from typing import Literal, List, Dict, Any

class SkillInput(BaseModel):
    task_id: str
    timestamp: float
    source: str
    payload: Dict[str, Any]
    context: Dict[str, Any]

class SkillOutput(BaseModel):
    task_id: str
    status: Literal["SUCCESS", "FAIL", "PARTIAL"]
    result: Dict[str, Any]
    logs: List[str]
    metrics: Dict[str, Any]

class SafetyResponse(BaseModel):
    decision: Literal["PASS", "BLOCK", "REQUIRE_SIMULATION"]
    reason: str
    risk_level: int = Field(..., ge=0, le=10)

class Task(BaseModel):
    id: str
    goal: str
    priority: int
    steps: List[str]
    state: Literal["PENDING", "RUNNING", "FAILED", "COMPLETED"]

