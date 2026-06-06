from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    detail: str = Field(description="Human-readable error message", examples=["Resource not found"])
    code: str = Field(description="Machine-readable error code", examples=["NOT_FOUND"])
    status: int = Field(description="HTTP status code", examples=[404])
