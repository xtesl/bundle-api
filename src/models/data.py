from enum import Enum
from typing import Any, Optional, List
from datetime import datetime

from sqlmodel import SQLModel, Field



class UserRole(str, Enum):
    ADMIN = "admin"
    REGULAR = "regular"
    AGENT = "agent"


class WalletTransactionType(str, Enum):
    TOPUP = "topup"
    PURCHASE = "purchase"
    COMMISSION = "commission"
    WITHDRAWAL = "withdrawal"


class PlanAudience(str, Enum):
    REGULAR = "regular"
    AGENT = "agent"


class ResponseStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"


class UserCreate(SQLModel):
    email: str
    password: str

class UserUpdate(SQLModel):
    is_active: bool | None = None
    role: UserRole | None = None
    

class EmailUserLogin(SQLModel):
    email: str
    password: str


class TokenPayload(SQLModel):
    sub: Optional[str] = None

class UserProfileCreate(SQLModel):
    name: Optional[str] = None
    phone: Optional[str] = None


class UserProfileRead(SQLModel):
    name: Optional[str]
    phone: Optional[str]

    class Config:
        from_attributes = True

class UserPublic(SQLModel):
    id: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime
    profile: Optional[UserProfileRead] = None

    class Config:
        from_attributes = True

class WalletRead(SQLModel):
    balance: float

    class Config:
        from_attributes = True

class WalletTransactionRead(SQLModel):
    id: str
    amount: float
    transaction_type: WalletTransactionType
    reference: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class InitializePayment(SQLModel):
    amount: float                     # in kobo
    payment_for: str                # "topup" | "agent_upgrade"


class VerifyPayment(SQLModel):
    reference: str

class NetworkCreate(SQLModel):
    name: str
    is_active: bool = True


class NetworkRead(SQLModel):
    id: str
    name: str
    is_active: bool

    class Config:
        from_attributes = True

class BundlePlanCreate(SQLModel):
    network_id: str
    value: str
    duration: str
    base_price: float
    audience: PlanAudience


class BundlePlanUpdate(SQLModel):
    network_id: str 
    value: str 
    duration: str 
    base_price: float 
    audience: PlanAudience 



class BundlePlanRead(SQLModel):
    id: str
    value: str
    duration: str
    base_price: float
    audience: PlanAudience
    is_active: bool

    class Config:
        from_attributes = True

class AgentStorefrontCreate(SQLModel):
    slug: str
    name: str

class AgentStorefrontUpdate(SQLModel):
    slug: str | None = None
    name: str | None = None
    is_active: bool | None = None

class AgentStorefrontRead(SQLModel):
    slug: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class AgentPlanPriceCreate(SQLModel):
    plan_id: str
    price: float


class AgentPlanPriceRead(SQLModel):
    plan_id: str
    price: float
    is_active: bool

    class Config:
        from_attributes = True

class OrderCreate(SQLModel):
    plan_id: str
    beneficiary_number: str


class CreatePaymentRequest(SQLModel):
    amount: float
    receiver_number: str
    mobilemoney_name: str

class WalletUpdate(SQLModel):
    new_balance: float
    email: str


class BuyBundle(OrderCreate):
    package_size: str
    external_id: str

class BuyBundleFromAgent(OrderCreate):
    payment_for: str


class UpdatePaymentRequest(SQLModel):
    status: str | None = None


class OrderRead(SQLModel):
    id: str
    plan_id: str
    beneficiary_number: str
    price_paid: float
    status: str
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True

class DashboardSummary(SQLModel):
    wallet_balance: float
    total_orders: int
    completed_orders: int

class SimpleResponse(SQLModel):
    status: ResponseStatus = ResponseStatus.SUCCESS
    status_code: int = 200
    message: Optional[str] = None
    data: Optional[Any] = None

class OffsetPagination(SQLModel):
    offset: int = 0
    limit: int = 10


class PaginationResponse(SQLModel):
    data: List[Any]
    pagination: dict





