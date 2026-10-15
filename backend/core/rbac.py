from enum import StrEnum


class Role(StrEnum):
    # "admin" is lowercase to match existing DB rows and the frontend check.
    ADMIN = "admin"
    AUDITOR = "Auditor"
    GATEKEEPER = "Gatekeeper"
    STRATEGIST = "Strategist"


ROLE_SCOPES: dict[Role, dict[str, object]] = {
    Role.ADMIN: {"description": "Manage users", "can_approve": False, "scope": "users"},
    Role.AUDITOR: {"description": "Review findings", "can_approve": True, "scope": "all"},
    Role.GATEKEEPER: {"description": "Control ingestion", "can_approve": False, "scope": "documents"},
    Role.STRATEGIST: {"description": "Portfolio decisions", "can_approve": False, "scope": "aggregated"},
}

