from pydantic import BaseModel, Field


class RiskPart(BaseModel):
    label: str
    value: int
    weight: str


class ForecastPoint(BaseModel):
    week: str
    actual: int | None = None
    predicted: int


class Vendor(BaseModel):
    id: str
    name: str
    category: str
    risk: int
    trend: int
    on_time: int = Field(serialization_alias="onTime")
    anomalies: int
    exposure: str
    risk_parts: list[RiskPart] = Field(serialization_alias="riskParts")
    forecast: list[ForecastPoint]
    expected_delay_days: float = Field(serialization_alias="expectedDelayDays")
    confidence_interval: str = Field(serialization_alias="confidenceInterval")
    pos_at_risk: int = Field(serialization_alias="posAtRisk")

