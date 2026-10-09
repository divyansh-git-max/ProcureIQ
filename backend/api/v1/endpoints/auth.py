import uuid
from typing import List

import bcrypt as py_bcrypt
from fastapi import APIRouter, Depends, HTTPException

from core.rbac import Role
from core.security import CurrentUser, create_token_pair, get_refresh_claims, require_roles
from db.session import get_pool
from schemas.auth import (
    ContactMessageRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
    UserStatusUpdate,
)

router = APIRouter()

require_admin = require_roles(Role.ADMIN)


@router.post("/signup", response_model=UserResponse)
async def signup(user: UserCreate):
    async with get_pool().acquire() as conn:
        existing_user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", user.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        user_id = str(uuid.uuid4())
        salt = py_bcrypt.gensalt()
        hashed_pw = py_bcrypt.hashpw(user.password.encode('utf-8'), salt).decode('utf-8')

        # New signups default to pending status
        status = "pending"

        await conn.execute(
            """
            INSERT INTO users (id, name, email, password_hash, role, status)
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            user_id, user.name, user.email, hashed_pw, user.role, status
        )

        row = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
        print(dict(row))
        return dict(row)

@router.post("/login", response_model=TokenResponse)
async def login(user: UserLogin):
    async with get_pool().acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM users WHERE email = $1", user.email)
        if not row:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        if not py_bcrypt.checkpw(user.password.encode('utf-8'), row["password_hash"].encode('utf-8')):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        if row["status"] == "rejected":
            raise HTTPException(status_code=403, detail="Your account request was rejected. Contact admin.")

        if row["status"] == "pending":
            raise HTTPException(status_code=403, detail="Your account request is still pending approval.")

        tokens = create_token_pair(row["id"], row["email"], row["role"])
        return {**tokens, "user": dict(row)}

@router.get("/users", response_model=List[UserResponse])
async def get_users(admin: CurrentUser = Depends(require_admin)):
    # TODO: Add pagination

    async with get_pool().acquire() as conn:
        rows = await conn.fetch("SELECT * FROM users ORDER BY created_at DESC")
        return [dict(r) for r in rows]

@router.patch("/users/{user_id}/status", response_model=UserResponse)
async def update_user_status(
    user_id: str, update: UserStatusUpdate, admin: CurrentUser = Depends(require_admin)
):
    async with get_pool().acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
        if not row:
            raise HTTPException(status_code=404, detail="User not found")

        role = update.role if update.role else row["role"]

        await conn.execute(
            "UPDATE users SET status = $1, role = $2 WHERE id = $3",
            update.status, role, user_id
        )

        updated_row = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
        return dict(updated_row)

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(claims: CurrentUser = Depends(get_refresh_claims)):
    return create_token_pair(claims.id, claims.email, claims.role)

@router.post("/contact")
async def user_request(payload: ContactMessageRequest):
    async with get_pool().acquire() as conn:
        user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", payload.email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        await conn.execute(
            "UPDATE users SET request_message = $1 WHERE email = $2",
            payload.message, payload.email
        )
        return {"status": "success", "message": "Contact message updated"}

@router.delete("/users/{user_id}")
async def delete_user(user_id: str, admin: CurrentUser = Depends(require_admin)):
    async with get_pool().acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
        if not row:
            raise HTTPException(status_code=404, detail="User not found")

        await conn.execute("DELETE FROM users WHERE id = $1", user_id)
        return {"status": "success", "message": "User deleted"}
