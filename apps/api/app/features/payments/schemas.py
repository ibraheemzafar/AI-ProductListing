from pydantic import BaseModel, Field


class CheckoutSessionRequest(BaseModel):
    plan_code: str = Field(min_length=1, max_length=50)


class CheckoutSessionResponse(BaseModel):
    url: str


class PortalSessionResponse(BaseModel):
    url: str
