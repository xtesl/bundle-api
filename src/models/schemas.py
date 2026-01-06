from uuid import uuid4
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from enum import Enum

from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, Numeric

id_field = Field(primary_key=True, default_factory=lambda: str(uuid4()))



class UserRole(str, Enum):
    ADMIN = "admin"
    REGULAR = "regular"
    AGENT = "agent"

class WalletTransactionType(str, Enum):
    TOPUP = "topup"
    PURCHASE = "purchase"

class PlanAudience(str, Enum):
    REGULAR = "regular"
    AGENT = "agent"

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[str] = id_field
    email: str = Field(index=True, unique=True)
    password_hash: str

    role: UserRole = Field(default=UserRole.REGULAR)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    profile: Optional["UserProfile"] = Relationship(back_populates="user")
    wallet: Optional["Wallet"] = Relationship(back_populates="user")

    customer_orders: List["Order"] = Relationship(
        back_populates="customer",
        sa_relationship_kwargs={
            "foreign_keys": "[Order.customer_id]"
        }
    )

    agent_orders: List["Order"] = Relationship(
        back_populates="agent",
        sa_relationship_kwargs={
            "foreign_keys": "[Order.agent_id]"
        }
    )


class PaymentRequest(SQLModel, table=True):
    __tablename__ = "payment_requets"

    id: Optional[str] = id_field
    agent_id: str = Field(foreign_key="users.id")
    amount: Decimal = Field(sa_column=Column(Numeric(12, 2)))
    receiver_number: str
    mobilemoney_name: str
    email: str
    status: str 
    
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserProfile(SQLModel, table=True):
    __tablename__ = "user_profiles"

    id: Optional[str] = id_field
    user_id: str = Field(foreign_key="users.id", unique=True)

    name: Optional[str] = None
    phone: Optional[str] = None

    user: User = Relationship(back_populates="profile")


class Wallet(SQLModel, table=True):
    __tablename__ = "wallets"

    id: Optional[str] = id_field
    user_id: str = Field(foreign_key="users.id", unique=True)

    balance: Decimal = Field(
        default=0,
        sa_column=Column(Numeric(12, 2))
    )

    user: User = Relationship(back_populates="wallet")

class Transaction(SQLModel, table=True):
    __tablename__ = "transactions"

    id: Optional[str] = id_field
    user_id: str = Field(foreign_key="users.id")

    amount: Decimal = Field(sa_column=Column(Numeric(12, 2)))
    transaction_type: WalletTransactionType
    reference: Optional[str] = None
    status: Optional[str] = "complete"

    created_at: datetime = Field(default_factory=datetime.utcnow)

 

class Network(SQLModel, table=True):
    __tablename__ = "networks"

    id: Optional[str] = id_field
    name: str
    is_active: bool = Field(default=True)

    plans: List["BundlePlan"] = Relationship(back_populates="network")


class BundlePlan(SQLModel, table=True):
    __tablename__ = "bundle_plans"

    id: Optional[str] = id_field
    creator_id: str = Field(foreign_key="users.id")
    network_id: str = Field(foreign_key="networks.id")

    value: str          # e.g. "5GB"
    duration: str       # e.g. "30 days"

    base_price: Decimal = Field(
        sa_column=Column(Numeric(10, 2))
    )

    audience: PlanAudience = Field(default=PlanAudience.REGULAR)
    is_active: bool = Field(default=True)

    network: Network = Relationship(back_populates="plans")


class AgentStorefront(SQLModel, table=True):
    __tablename__ = "agent_storefronts"

    id: Optional[str] = id_field
    agent_id: str = Field(foreign_key="users.id", unique=True)
    name: str = Field(index=True)

    slug: str = Field(index=True, unique=True)  # public URL
    is_active: bool = Field(default=True)

    created_at: datetime = Field(default_factory=datetime.utcnow)



class Order(SQLModel, table=True):
    __tablename__ = "orders"

    id: Optional[str] = id_field

    customer_id: str = Field(foreign_key="users.id")
    agent_id: Optional[str] = Field(default=None, foreign_key="users.id")

    plan_id: str = Field(foreign_key="bundle_plans.id")
    beneficiary_number: str

    price_paid: Decimal = Field(sa_column=Column(Numeric(10, 2)))
    status: str = Field(default="pending")
    external_id: str 

    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    customer: User = Relationship(
        back_populates="customer_orders",
        sa_relationship_kwargs={
            "foreign_keys": "[Order.customer_id]"
        }
    )

    agent: Optional[User] = Relationship(
        back_populates="agent_orders",
        sa_relationship_kwargs={
            "foreign_keys": "[Order.agent_id]"
        }
    )

















