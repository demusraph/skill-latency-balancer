from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
import uuid

class TaskRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    
    task_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    skill_name: str
    priority: int = Field(ge=0, le=10, default=5)
    payload: dict
    created_at: datetime = Field(default_factory=datetime.utcnow)

class TelemetryMetric(BaseModel):
    latency_ms: float
    queue_depth: int
    throttle_limit: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ExecutionResult(BaseModel):
    task_id: uuid.UUID
    status: str
    execution_time_ms: float
    error: Optional[str] = None