from fastapi import APIRouter

from src.router.user import api_router as user_router
from src.router.management import api_router as management_router
from src.router.order import api_router as order_router
from src.router.payment import api_router as payment_router

api_router = APIRouter()

api_router.include_router(user_router, prefix="/users", tags=["user"])
api_router.include_router(management_router, prefix="/management", tags=["management"])
api_router.include_router(order_router, prefix="/orders", tags=['order'])
api_router.include_router(payment_router, prefix="/payments", tags=['payment'])