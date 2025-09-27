from enum import Enum
from typing import Any, Optional
from datetime import datetime

from sqlmodel import SQLModel, Field

from src.models.schemas import UserType

class UserCreate(SQLModel):
    name: str | None = None
    email: str
    phone: str | None = None
    user_type: UserType
    password: str
    parent_id: str | None = None

class UserPublic(SQLModel):
    name: str | None = None
    account_balance: float
    email: str
    phone: str | None = None
    user_type: UserType

class EmailUserLogin(SQLModel):
    email: str
    password: str

class PlanCreate(SQLModel):
    price: float
    value: str
    duration: str
    network_id: str 

class NetworkCreate(SQLModel):
    name: str
    is_active: bool = True

class OrderCreate(SQLModel):
    beneficiary_number: str
    plan_id: str 
    network_name: str
    data_amount: str


class InitializePayment(SQLModel):
    email: str
    amount: str
    payment_for: str # i.e agent-reg, topup
    purchase_info: OrderCreate

class BundlePlanBase(SQLModel):
    id: str
    price: float
    value: str
    duration: str

class BundlePlanRead(SQLModel):
    id: str
    price: float
    value: str
    duration: str

    class Config:
        from_attributes = True 


class OrderBase(SQLModel):
    id: str
    beneficiary_number: str
    customer_id: str
    plan_id: str
    completed: Optional[bool]
    created_at: datetime
    completed_at: Optional[datetime]


class OrderRead(SQLModel):
    id: str
    beneficiary_number: str
    customer_id: str
    plan_id: str
    completed: Optional[bool]
    created_at: datetime
    completed_at: Optional[datetime]
    plan: Optional[BundlePlanRead] = None

    class Config:
        from_attributes = True  

class OrderUpdate(SQLModel):
    completed: bool | None = None
    
class ResponseStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"

class TokenPayload(SQLModel):
    sub: str | None = None

class SimpleResponse(SQLModel):
    status: ResponseStatus = ResponseStatus.SUCCESS
    status_code: int = 200
    message: str | None = None
    data: Any | None = None

class PaginationResponse(SQLModel):
    data: list[Any]
    pagination: dict

class OffsetPagination(SQLModel):
    offset: int = 0,
    limit: int = 10