from fastapi_utils.cbv import cbv
from fastapi import APIRouter, status, Response
from fastapi.exceptions import HTTPException
from sqlalchemy.orm import selectinload

from src.base_router import BaseRouter
from src.models.data import PlanCreate, NetworkCreate, OrderRead, OrderUpdate
from src.models.schemas import BundlePlan, UserType, Network, Order
from src.utils.database import save, get_objects, get_objects_v2, get_object_or_404, update_object, delete
from src.api.deps import CurrentUser

api_router = APIRouter()


@cbv(api_router)
class ManagementRouter(BaseRouter):
    @api_router.post("/create-plan")
    async def create_plan(self, plan_data: PlanCreate, current_user: CurrentUser):
        # Only Admins are allowed
        if current_user.user_type is not UserType.ADMIN:
            raise HTTPException(
                401
            )
        
        validated_data = BundlePlan.model_validate(plan_data)
        plan_db = await save(self.session, validated_data, True)
        return plan_db

    @api_router.post('/networks')
    async def create_network(self, current_user: CurrentUser, network_data: NetworkCreate):
        if current_user.user_type is not UserType.ADMIN: 
            raise HTTPException(
                401
            )
        
        validated_data = Network.model_validate(network_data)
        network_db = await save(self.session, validated_data, True)
        return network_db

    @api_router.get("/networks")
    async def read_networks(self):
        return await get_objects(
            self.session,
            model=Network
        )
    
    @api_router.get("/plans/{network_id}")
    async def read_network_plans(self, network_id: str):
        return await get_objects(
            self.session,
            model=BundlePlan,
            filter_by=(BundlePlan.network_id, network_id)
        )
    
    @api_router.get("/orders")
    async def read_orders(self, current_user: CurrentUser):
        orders = await get_objects_v2(
                  session=self.session,
                  model=Order,
                  options=[selectinload(Order.plan)]  # This will eager load the plan relationship
      )
        return [OrderRead.model_validate(o) for o in orders]
    

    @api_router.patch("/orders/{order_id}")
    async def updated_orders(self, current_user: CurrentUser, body: OrderUpdate, order_id: str):
        order = await get_object_or_404(
            self.session,
            where_attr=Order.id,
            where_value=order_id
        )
        return await update_object(
            self.session,
            body.model_dump(exclude_unset=True),
            order
        )
    
    @api_router.delete("/management/orders/{order_id}")
    async def delete_order(self, current_user: CurrentUser, order_id: str):
        order_db = await get_object_or_404(
            self.session,
            where_attr=Order.id,
            where_value=order_id, 
        )
        await delete(self.session, order_db)
        

