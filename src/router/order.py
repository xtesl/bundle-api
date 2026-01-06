from fastapi_utils.cbv import cbv
from fastapi import APIRouter, status, Response
from fastapi.exceptions import HTTPException
from sqlalchemy.orm import selectinload

from src.base_router import BaseRouter
from src.models.data import BundlePlanCreate, NetworkCreate, OrderCreate, OrderRead
from src.models.schemas import BundlePlan, UserRole, Network, Order
from src.utils.database import save, get_objects, get_objects_v2, sync_orders_with_external
from src.utils.helpers import make_request
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

        orders = await get_objects(
                  session=self.session,
                  model=Order,
                  filter_by=(Order.customer_id, current_user.id),
                 
        )

        if not orders:
            return []


        url = "https://www.blessdatahub.com/api/check_order_status.php?order_ids="
        orders_size = len(orders)
        for index, order in enumerate(orders):
            url += f"{order.external_id}"
            if index < orders_size - 1:
                url += ","         


        res = make_request(
                    "GET",
                    url,
                    headers={
                            "Content-Type": "application/json", 
                             "Authorization": "Bearer XUBeGct8zRgnaqMmlmGxZBOZ1zmKVHeI"
                        }
                    )
        
        if res.get("status_code"):
            if res["status_code"] == 200:
                external_orders = res['data']['orders']
                return await sync_orders_with_external(self.session, orders, external_orders)

        else:
            raise HTTPException(
                500,
                "Something went wrong. Please try again."
            )


    
       

   

        