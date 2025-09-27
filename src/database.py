import os
from urllib.parse import quote_plus
from dotenv import load_dotenv
from pydantic import AnyUrl
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker

# Load env vars
load_dotenv()

# Read database mode: "mysql" or "sqlite"
DB_MODE = os.getenv("DB_MODE", "mysql").lower()

MYSQL_SERVER = os.getenv("MYSQL_SERVER")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DB = os.getenv("MYSQL_DB")


def generate_mysql_async_uri(
    password: str, username: str, port: int, host: str, db_name: str
) -> AnyUrl:
    """Generates an async database URI for MySQL using aiomysql driver."""
    encoded_password = quote_plus(password or "")
    return f"mysql+aiomysql://{username}:{encoded_password}@{host}:{port}/{db_name}"


def generate_sqlite_async_uri() -> str:
    """Generates an async database URI for SQLite."""
    return "sqlite+aiosqlite:///./test.db"  # file-based SQLite (fast + persists)


# Choose DB URL based on mode
if DB_MODE == "sqlite":
    DATABASE_URL = generate_sqlite_async_uri()
else:
    DATABASE_URL = generate_mysql_async_uri(
        password=MYSQL_PASSWORD,
        username=MYSQL_USER,
        port=int(MYSQL_PORT),
        host=MYSQL_SERVER,
        db_name=MYSQL_DB,
    )


# Create async engine with optimized pooling
engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=False,  # set to True for SQL debug logs
    future=True,
    pool_size=10,        # up to 10 connections in pool
    max_overflow=20,     # can borrow 20 extra if load spikes
    pool_timeout=30,     # wait 30s before giving up
    pool_recycle=1800,   # recycle connections every 30 min
)

# Async session factory
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def init_db() -> None:
    """Initialize database (create tables)."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
