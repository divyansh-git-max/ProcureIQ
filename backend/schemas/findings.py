from enum import Enum

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
    status: FindingStatus


class DecisionResponse(BaseModel):
    finding_id: str = Field(serialization_alias="id")
    status: FindingStatus

