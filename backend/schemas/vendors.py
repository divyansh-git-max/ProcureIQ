from pydantic import BaseModel, Field
from pydantic import ConfigDict


class RiskPart(BaseModel):
    label: str
    value: int
    weight: str


class ForecastPoint(BaseModel):
    week: str
    actual: int | None = None
    predicted: int


class Vendor(BaseModel):
    # populate_by_name=True lets Pydantic accept snake_case (from DB rows)
    # while still serializing to camelCase (for the frontend)
    model_config = ConfigDict(populate_by_name=True)

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


class VendorCreate(BaseModel):
    """Used by Admin/Auditor POST /vendors and by doc_intel auto-creation."""
    name: str
    category: str = "Unknown"
    risk: int = 0
    trend: int = 0
    on_time: int = 100
    anomalies: int = 0
    exposure: str = "Low"
    risk_parts: list[RiskPart] = Field(default_factory=list)
    forecast: list[ForecastPoint] = Field(default_factory=list)
    expected_delay_days: float = 0.0
    confidence_interval: str = "N/A"
    pos_at_risk: int = 0


class VendorRiskUpdate(BaseModel):
    """Payload for upsert_risk_score — written back by the risk scoring agent."""
    risk: int
    trend: int
    delivery_delay_rate: float
    invoice_anomaly_rate: float
    contract_compliance_score: float
    external_reputation_score: float
