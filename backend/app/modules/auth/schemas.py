from typing import Literal

from pydantic import BaseModel, Field

from app.modules.users.schemas import UserRead
from app.shared.schemas import Email


class LoginRequest(BaseModel):
    email: Email
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int = Field(description="Segundos hasta que caduca el access token")
    user: UserRead
