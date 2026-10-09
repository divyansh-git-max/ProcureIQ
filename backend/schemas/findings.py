from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class FindingStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DISMISSED = "dismissed"


class Finding(BaseModel):
    id: str
    severity: str
    title: str
    vendor: str
    amount: str
    confidence: int
    source: str
    clause: str
    detail: str
    reasoning_steps: list[str] = Field(serialization_alias="reasoningSteps")
    agent_path: list[str] = Field(serialization_alias="agentPath")
    status: FindingStatus


class DecisionRequest(BaseModel):
    # A decision is final: "pending" is not a valid target.
    status: Literal[FindingStatus.APPROVED, FindingStatus.DISMISSED]
    note: str | None = Field(default=None, max_length=500)


class DecisionResponse(BaseModel):
    finding_id: str = Field(serialization_alias="id")
    status: FindingStatus
    resolved_at: datetime = Field(serialization_alias="resolvedAt")

