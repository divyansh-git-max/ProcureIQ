import datetime
from datetime import timezone

import jwt
import pytest

from config import settings
from core.rbac import Role
from core.security import ALGORITHM, decode_token
from tests.conftest import bearer, db_execute, insert_user


def test_tokens_carry_type_claim() -> None:
    access = bearer(Role.AUDITOR)["Authorization"].split()[1]
    refresh = bearer(Role.AUDITOR, "refresh")["Authorization"].split()[1]
    assert jwt.decode(access, settings.secret_key, algorithms=[ALGORITHM])["type"] == "access"
    assert jwt.decode(refresh, settings.secret_key, algorithms=[ALGORITHM])["type"] == "refresh"


def test_admin_route_requires_token(client) -> None:
    assert client.get("/api/v1/auth/users").status_code == 401


@pytest.mark.parametrize("role", [Role.AUDITOR, Role.GATEKEEPER, Role.STRATEGIST])
def test_admin_route_rejects_non_admin_roles(client, role) -> None:
    response = client.get("/api/v1/auth/users", headers=bearer(role))
    assert response.status_code == 403


def test_admin_route_rejects_refresh_token(client) -> None:
    response = client.get("/api/v1/auth/users", headers=bearer(Role.ADMIN, "refresh"))
    assert response.status_code == 401


def test_admin_route_rejects_token_signed_with_other_key(client) -> None:
    forged = jwt.encode(
        {"sub": "x", "email": "a@b.c", "role": "admin", "type": "access"},
        "secret_key",
        algorithm=ALGORITHM,
    )
    response = client.get("/api/v1/auth/users", headers={"Authorization": f"Bearer {forged}"})
    assert response.status_code == 401


def test_legacy_token_without_type_rejected(client) -> None:
    legacy = jwt.encode(
        {"sub": "x", "email": "a@b.c", "role": "admin"}, settings.secret_key, algorithm=ALGORITHM
    )
    response = client.get("/api/v1/auth/users", headers={"Authorization": f"Bearer {legacy}"})
    assert response.status_code == 401


def test_expired_token_rejected() -> None:
    expired = jwt.encode(
        {
            "sub": "x",
            "email": "a@b.c",
            "role": "admin",
            "type": "access",
            "exp": datetime.datetime.now(timezone.utc) - datetime.timedelta(minutes=1),
        },
        settings.secret_key,
        algorithm=ALGORITHM,
    )
    with pytest.raises(Exception) as exc_info:
        decode_token(expired, "access")
    assert exc_info.value.status_code == 401


def test_refresh_endpoint_rejects_access_token(client) -> None:
    response = client.post("/api/v1/auth/refresh", headers=bearer(Role.AUDITOR))
    assert response.status_code == 401


@pytest.mark.db
def test_admin_route_allows_admin(db_client) -> None:
    response = db_client.get("/api/v1/auth/users", headers=bearer(Role.ADMIN))
    assert response.status_code == 200


@pytest.mark.db
def test_refresh_reissues_tokens_with_current_db_role(db_client) -> None:
    user_id = insert_user(Role.GATEKEEPER)
    db_execute("UPDATE users SET role = $1 WHERE id = $2", Role.AUDITOR.value, user_id)

    response = db_client.post(
        "/api/v1/auth/refresh", headers=bearer(Role.GATEKEEPER, "refresh", sub=user_id)
    )

    assert response.status_code == 200
    claims = decode_token(response.json()["access_token"], "access")
    assert claims.role == Role.AUDITOR


@pytest.mark.db
@pytest.mark.parametrize("status", ["rejected", "pending"])
def test_refresh_rejects_blocked_users(db_client, status) -> None:
    user_id = insert_user(Role.AUDITOR, status=status)
    response = db_client.post(
        "/api/v1/auth/refresh", headers=bearer(Role.AUDITOR, "refresh", sub=user_id)
    )
    assert response.status_code == 401


@pytest.mark.db
def test_refresh_rejects_deleted_user(db_client) -> None:
    response = db_client.post(
        "/api/v1/auth/refresh", headers=bearer(Role.AUDITOR, "refresh", sub="no-such-user")
    )
    assert response.status_code == 401
