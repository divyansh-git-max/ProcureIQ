from pydantic import BaseModel, Field


class Kpi(BaseModel):
    id: str
    label: str
    value: str
    delta: str
    tone: str
    foot: str


class WeeklyRiskPoint(BaseModel):
    day: str
    exposure: int
    resolved: int


class SeverityMixItem(BaseModel):
    name: str
    value: int
    color: str


class SummaryResponse(BaseModel):
    kpis: list[Kpi]
    weekly_risk: list[WeeklyRiskPoint] = Field(serialization_alias="weeklyRisk")
    severity_mix: list[SeverityMixItem] = Field(serialization_alias="severityMix")

