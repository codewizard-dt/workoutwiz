import uuid
from fastapi_users import schemas
from pydantic import EmailStr, Field


class UserRead(schemas.BaseUser[uuid.UUID]):
    id: uuid.UUID = Field(description="Unique user identifier (UUID)", examples=["a1b2c3d4-e5f6-7890-abcd-ef1234567890"])
    email: str = Field(description="User's email address", examples=["coach@example.com"])
    is_active: bool = Field(description="Whether the account is active", examples=[True])
    is_superuser: bool = Field(description="Whether the user has superuser privileges", examples=[False])
    is_verified: bool = Field(description="Whether the email address has been verified", examples=[True])


class UserCreate(schemas.BaseUserCreate):
    email: EmailStr = Field(description="Email address for the new account", examples=["coach@example.com"])
    password: str = Field(description="Password for the new account (min 8 characters)", examples=["S3cur3P@ss!"])
    is_active: bool | None = Field(default=True, description="Whether the account is active on creation", examples=[True])
    is_superuser: bool | None = Field(default=False, description="Whether the user has superuser privileges", examples=[False])
    is_verified: bool | None = Field(default=False, description="Whether the email address has been verified", examples=[False])


class UserUpdate(schemas.BaseUserUpdate):
    pass
