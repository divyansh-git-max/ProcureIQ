from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr

from core.rbac import Role

# Roles a user may request at signup. Admin is never self-assigned.
SignupRole = Literal[Role.AUDITOR, Role.GATEKEEPER, Role.STRATEGIST]
UserStatus = Literal["pending", "approved", "rejected", "flagged"]


class UserBase(BaseModel):
    name: str
    email: EmailStr

class UserCreate(UserBase):
    password: str
    role: SignupRole

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):   
    id: str
    role: str
    status: str
    request_message: Optional[str] = None
    created_at: datetime

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str
    user: Optional[UserResponse] = None

class UserStatusUpdate(BaseModel):
    status: UserStatus
    role: Optional[Role] = None

class ContactMessageRequest(BaseModel):
    email: EmailStr
    message: str

class StatusResponse(BaseModel):
    status: str
    message: str
