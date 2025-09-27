from fastapi_utils.cbv import cbv
from fastapi import APIRouter, status, Response
from fastapi.exceptions import HTTPException
from sqlalchemy.orm import selectinload

from src.base_router import BaseRouter
from src.models.data import PlanCreate, NetworkCreate, OrderCreate, OrderRead
from src.models.schemas import BundlePlan, UserType, Network, Order
from src.utils.database import save, get_objects, get_objects_v2
from src.api.deps import CurrentUser


api_router = APIRouter()


@cbv(api_router)
class OrderRouter(BaseRouter):
    @api_router.post("/")
    async def create_order(self, order_data: OrderCreate, current_user: CurrentUser):
        validated_data = Order.model_validate(order_data, update={
            "customer_id": current_user.id
        })
        order_db = await save(self.session, validated_data, True)
        return order_db
    
    @api_router.get("/me")
    async def get_my_orders(self, current_user: CurrentUser):

        orders = await get_objects_v2(
                  session=self.session,
                  model=Order,
                  where_clauses=[Order.customer_id == current_user.id],
                  options=[selectinload(Order.plan)]  # This will eager load the plan relationship
      )
        return [OrderRead.model_validate(o) for o in orders]

   

        