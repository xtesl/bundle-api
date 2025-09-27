import os
from urllib.parse import quote_plus
from dotenv import load_dotenv
from pydantic import AnyUrl
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker

# Import your models so SQLModel.metadata includes them


# Load env vars
load_dotenv()

MYSQL_SERVER = os.getenv("MYSQL_SERVER")
MYSQL_PORT = os.getenv("MYSQL_PORT")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DB = os.getenv("MYSQL_DB")

def generate_mysql_async_uri(
    password: str, username: str, port: int, host: str, db_name: str
) -> AnyUrl:
    """
    Generates an async database URI for MySQL database using aiomysql driver.
    """
    encoded_password = quote_plus(password)
    return f"mysql+aiomysql://{username}:{encoded_password}@{host}:{port}/{db_name}"

# Create async engine
engine: AsyncEngine = create_async_engine(
    generate_mysql_async_uri(
        password=MYSQL_PASSWORD,
        username=MYSQL_USER,
        port=int(MYSQL_PORT),
        host=MYSQL_SERVER,
        db_name=MYSQL_DB
    ),
    echo=True,
    future=True
)


async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def init_db() -> None:
    """
    Initialize the database (create tables) using async engine.
    """
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
