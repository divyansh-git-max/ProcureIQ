import pytest

from core.rbac import Role
from tests.conftest import bearer, db_execute, insert_user

SIGNUP = {"name": "New User", "email": "new@example.com", "password": "pw-123456"}


@pytest.mark.parametrize("role", ["admin", "Admin", "Superuser", ""])
def test_signup_rejects_admin_and_unknown_roles(client, role) -> None:
    response = client.post("/api/v1/auth/signup", json={**SIGNUP, "role": role})
    assert response.status_code == 422


def test_status_update_rejects_unknown_status(client) -> None:
    response = client.patch(
        "/api/v1/auth/users/any/status", json={"status": "superuser"}, headers=bearer(Role.ADMIN)
    )
    assert response.status_code == 422


def test_status_update_rejects_unknown_role(client) -> None:
    response = client.patch(
        "/api/v1/auth/users/any/status",
        json={"status": "approved", "role": "root"},
        headers=bearer(Role.ADMIN),
    )
    assert response.status_code == 422


@pytest.mark.db
def test_signup_creates_pending_user_with_requested_role(db_client) -> None:
    email = "signup-ok@example.com"
    db_execute("DELETE FROM users WHERE email = $1", email)

    response = db_client.post(
        "/api/v1/auth/signup", json={**SIGNUP, "email": email, "role": "Gatekeeper"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["role"] == "Gatekeeper"
    assert body["status"] == "pending"
    assert "password_hash" not in body


@pytest.mark.db
def test_admin_can_flag_user(db_client) -> None:
    user_id = insert_user(Role.STRATEGIST, status="pending")
    response = db_client.patch(
        f"/api/v1/auth/users/{user_id}/status",
        json={"status": "flagged"},
        headers=bearer(Role.ADMIN),
    )
    assert response.status_code == 200
    assert response.json()["status"] == "flagged"
