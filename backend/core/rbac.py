from enum import StrEnum


class Role(StrEnum):
    AUDITOR = "Auditor"
    GATEKEEPER = "Gatekeeper"
    STRATEGIST = "Strategist"


ROLE_SCOPES: dict[Role, dict[str, object]] = {
    Role.AUDITOR: {"description": "Review findings", "can_approve": True, "scope": "all"},
    Role.GATEKEEPER: {"description": "Control ingestion", "can_approve": False, "scope": "documents"},
    Role.STRATEGIST: {"description": "Portfolio decisions", "can_approve": False, "scope": "aggregated"},
}

