import uuid
import datetime
from datetime import timezone
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

import bcrypt as py_bcrypt
import jwt
from typing import List

from db.session import get_pool
from schemas.auth import UserCreate, UserLogin, UserResponse, TokenResponse, UserStatusUpdate, ContactMessageRequest, StatusResponse
from config import settings

router = APIRouter()

SECRET_KEY = getattr(settings, "secret_key", "dev_secret_key_change_me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 1 week

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.datetime.now(timezone.utc) + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.datetime.now(timezone.utc) + datetime.timedelta(days=7)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_admin_user(token: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("email")
        role = payload.get("role")
        if email is None and role != "admin":
            raise HTTPException(status_code=403, detail="Forbidden")
        return email
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

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
        print("===========================================================")
        print(dict(row))
        print("===========================================================")
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
            
        access_token = create_access_token(data={"sub": row["id"], "email": row["email"], "role": row["role"]})
        refresh_token = create_refresh_token(data={"sub": row["id"], "email": row["email"], "role": row["role"]})
        
        user_response = dict(row)
        return {"access_token": access_token, "refresh_token": refresh_token ,"token_type": "bearer", "user": user_response}

@router.get("/users", response_model=List[UserResponse])
async def get_users(admin: dict = Depends(get_current_admin_user)):
    # In a real app we'd require admin token dependency here

    # TODO: Add pagination
    
    async with get_pool().acquire() as conn:
        rows = await conn.fetch("SELECT * FROM users ORDER BY created_at DESC")
        return [dict(r) for r in rows]

@router.patch("/users/{user_id}/status", response_model=UserResponse)
async def update_user_status(user_id: str, update: UserStatusUpdate, admin: dict = Depends(get_current_admin_user)):
    # Requires admin token dependency
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
async def refresh_token(token: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        email = payload.get("email")
        role = payload.get("role")
        if sub is None or email is None or role is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        access_token = create_access_token(data={"sub": sub, "email": email, "role": role})
        refresh_token = create_refresh_token(data={"sub": sub, "email": email, "role": role})
        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

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
async def delete_user(user_id: str, admin: dict = Depends(get_current_admin_user)):
    async with get_pool().acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
            
        await conn.execute("DELETE FROM users WHERE id = $1", user_id)
        return {"status": "success", "message": "User deleted"}
