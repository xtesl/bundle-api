from typing import AsyncGenerator, Annotated

from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import Depends, Request, status
from fastapi.exceptions import HTTPException

from src.database import async_session
from src.models.schemas import User
from src.models.data import TokenPayload
from src.utils.helpers import verify_jwt



async def get_async_session() -> AsyncGenerator[AsyncSession,  None]:
    async with async_session() as session:
        yield session


AsyncSessionDep = Annotated[AsyncSession, Depends(get_async_session)]


async def get_current_user(session: AsyncSessionDep, request: Request) -> User:
    """
    Retrieves access token from request cookies for authorization.
    """
    token = request.cookies.get("firstpoint_bundles-access-token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token is missing.",
            headers={
                "WWW-Authenticate": "Bearer realm=\"Access to protected API\""
            }
        )
    
    payload = verify_jwt(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token", 
            headers={"WWW-Authenticate": "Bearer error=\"invalid_token\""}
        )
    
    token_data = TokenPayload(**payload)
    user = await session.get(User, token_data.sub)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

CurrentUser = Annotated[User, Depends(get_current_user)]