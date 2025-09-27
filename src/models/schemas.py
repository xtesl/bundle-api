from uuid import uuid4
from enum import Enum
from datetime import datetime
from decimal import Decimal
from typing import List

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from sqlalchemy import Numeric, Column

class UserType(str, Enum):
    ADMIN = "admin"
    REGULAR = "regular"
    AGENT = 'agent'

id_field = Field(primary_key=True, default_factory=lambda: str(uuid4()))

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[str] = id_field
    account_balance: Optional[Decimal] = Field(default=0.00, sa_column=Column(Numeric(10, 2)))
    parent_id: Optional[str] = Field(foreign_key="users.id")
    password_hash: str
    name: Optional[str] = None
    email: str
    phone: Optional[str] = None
    is_active: bool = Field(default=True)
    user_type: UserType = Field(default=UserType.REGULAR)
    orders: List["Order"] = Relationship(back_populates="customer")

class Network(SQLModel, table=True):
    __tablename__ = "networks"

    id: Optional[str] = id_field
    name: str
    is_active: bool = Field(default=True)
    plans: List["BundlePlan"] = Relationship(back_populates="network")

class PlanType(str, Enum):
    REGULAR = "regular"
    AGENT = "agent"

class BundlePlan(SQLModel, table=True):
    __tablename__ = "bundle_plans"

    id: Optional[str] = id_field
    network_id: str = Field(foreign_key="networks.id")
    price: Decimal = Field(sa_column=Column(Numeric(10, 2)))
    value: str
    duration: str
    network: Network = Relationship(back_populates="plans")
    orders: List["Order"] = Relationship(back_populates="plan")
    plan_type: PlanType 

class Order(SQLModel, table=True):
    __tablename__ = "orders"

    id: Optional[str] = id_field
    beneficiary_number: str
    customer_id: str = Field(foreign_key="users.id")
    plan_id: str = Field(foreign_key="bundle_plans.id")
    plan: Optional[BundlePlan] = Relationship(back_populates="orders")
    completed: Optional[bool] = Field(default=False)
    customer: "User" = Relationship(back_populates="orders")
    created_at: Optional[datetime] = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = Field(default=None)

