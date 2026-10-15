"""JWT issuing/verification and role-based route dependencies."""

import datetime
from dataclasses import dataclass
from datetime import timezone
from typing import Literal

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from config import settings
from core.rbac import Role

ALGORITHM = "HS256"

TokenType = Literal["access", "refresh"]

# auto_error=False so a missing header becomes our 401 rather than FastAPI's default.
_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    id: str
    email: str
    role: str


def create_token(sub: str, email: str, role: str, token_type: TokenType) -> str:
    if token_type == "access":
        lifetime = datetime.timedelta(minutes=settings.access_token_minutes)
    else:
        lifetime = datetime.timedelta(days=settings.refresh_token_days)
    payload = {
        "sub": sub,
        "email": email,
        "role": role,
        "type": token_type,
        "exp": datetime.datetime.now(timezone.utc) + lifetime,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def create_token_pair(sub: str, email: str, role: str) -> dict[str, str]:
    return {
        "access_token": create_token(sub, email, role, "access"),
        "refresh_token": create_token(sub, email, role, "refresh"),
        "token_type": "bearer",
    }


def decode_token(raw: str, expected_type: TokenType) -> CurrentUser:
    """Verify signature, expiry and token type. Raises 401 on any failure."""
    try:
        payload = jwt.decode(raw, settings.secret_key, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    if payload.get("type") != expected_type:
        raise HTTPException(status_code=401, detail="Invalid token type")
    sub, email, role = payload.get("sub"), payload.get("email"), payload.get("role")
    if not sub or not email or not role:
        raise HTTPException(status_code=401, detail="Invalid token")
    return CurrentUser(id=sub, email=email, role=role)


def _credentials(credentials: HTTPAuthorizationCredentials | None) -> str:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return credentials.credentials


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> CurrentUser:
    return decode_token(_credentials(credentials), "access")


def get_refresh_claims(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> CurrentUser:
    return decode_token(_credentials(credentials), "refresh")


def require_roles(*roles: Role):
    allowed = {r.value for r in roles}

    def dependency(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in allowed:
            raise HTTPException(status_code=403, detail="Forbidden")
        return user

    return dependency
