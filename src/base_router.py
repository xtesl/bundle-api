from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import Session
from fastapi import Depends

from src.api.deps import get_async_session

class BaseRouter:
    def __init__(
            self,
            session: Session = Depends(get_async_session)
    ):
        self.session = session


    