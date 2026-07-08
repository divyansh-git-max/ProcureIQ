from pydantic import BaseModel, Field


class Slo(BaseModel):
    label: str
    value: str
    target: str


class LatencyPoint(BaseModel):
    time: str
    p50: int
    p95: int


class RagasMetric(BaseModel):
    label: str
    value: int
    inverse: bool = False


class TrajectoryEval(BaseModel):
    intent: str
    expected: list[str]
    actual: list[str]
    correct_route: bool = Field(serialization_alias="correctRoute")
    efficiency: int


class Trace(BaseModel):
    id: str
    action: str
    duration: str
    status: str
    agents: list[int]


class GuardrailLog(BaseModel):
    time: str
    level: str
    source: str
    message: str


class OperationsHealthResponse(BaseModel):
    slos: list[Slo]
    latency_data: list[LatencyPoint] = Field(serialization_alias="latencyData")
    ragas_metrics: list[RagasMetric] = Field(serialization_alias="ragasMetrics")
    trajectory_eval: list[TrajectoryEval] = Field(serialization_alias="trajectoryEval")
    traces: list[Trace]
    guardrail_log: list[GuardrailLog] = Field(serialization_alias="guardrailLog")

