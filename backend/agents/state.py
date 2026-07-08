from typing import TypedDict


class AgentState(TypedDict, total=False):
    request_id: str
    intent: str
    document_ids: list[str]
    vendor_id: str
    retrieved_chunks: list[dict[str, object]]
    findings: list[dict[str, object]]
    agent_path: list[str]

