import os
from urllib.parse import quote_plus
from dotenv import load_dotenv
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker

# Load env vars
load_dotenv()

DB_MODE = os.getenv("DB_MODE", "mysql").lower()

MYSQL_SERVER = os.getenv("MYSQL_SERVER")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DB = os.getenv("MYSQL_DB")


def generate_mariadb_async_uri() -> str:
    password = quote_plus(MYSQL_PASSWORD or "")
    return (
        f"mysql+aiomysql://{MYSQL_USER}:{password}"
        f"@{MYSQL_SERVER}:{MYSQL_PORT}/{MYSQL_DB}"
    )


def generate_sqlite_async_uri() -> str:
    return "sqlite+aiosqlite:///./test.db"


# Choose DB
if DB_MODE == "sqlite":
    DATABASE_URL = generate_sqlite_async_uri()
    engine: AsyncEngine = create_async_engine(
        DATABASE_URL,
        echo=False,
        future=True,
    )
else:
    DATABASE_URL = generate_mariadb_async_uri()
    engine: AsyncEngine = create_async_engine(
        DATABASE_URL,
        echo=False,
        future=True,
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
        pool_recycle=1800,
    )


async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
