from decimal import Decimal

from fastapi_utils.cbv import cbv
from fastapi import APIRouter, status, Response
from fastapi.exceptions import HTTPException
from sqlalchemy.orm import selectinload

from src.base_router import BaseRouter
from src.models.data import (
                            NetworkCreate, 
                            OrderRead, BundlePlanCreate, BundlePlanUpdate, AgentStorefrontCreate, 
                            AgentStorefrontUpdate, 
                            WalletUpdate,
                            UserPublic, 
                            UserUpdate,
                            UpdatePaymentRequest
                        )
from src.models.schemas import BundlePlan, UserRole, Network, Order, User, AgentStorefront, Wallet, PaymentRequest
from src.utils.database import save, get_objects, get_objects_v2, get_object_or_404, update_object, delete
from src.utils.helpers import generate_slug_from_name
from src.api.deps import CurrentUser

api_router = APIRouter()


@cbv(api_router)
class ManagementRouter(BaseRouter):
    @api_router.post("/create-package")
    async def create_plan(self, plan_data: BundlePlanCreate, current_user: CurrentUser):
        if current_user.role is  UserRole.REGULAR:
            raise HTTPException(
                401
            )
        
        validated_data = BundlePlan.model_validate(plan_data, update={"creator_id": current_user.id})
        plan_db = await save(self.session, validated_data, True)
        return plan_db
    
    @api_router.post("/storefronts")
    async def create_storefront(self, data: AgentStorefrontCreate, current_user: CurrentUser):
        # if current_user.role is UserRole.REGULAR:
        #     raise HTTPException(
        #         401
        #     )
        
        validated_data = AgentStorefront.model_validate(data, update={"agent_id": current_user.id})
        storefront_db = await save(self.session, validated_data, True)
        return storefront_db
    
    @api_router.get("/storefronts")
    async def get_storefront(self, current_user: CurrentUser):
        # if current_user.role is UserRole.REGULAR:
        #     raise HTTPException(
        #         401
        #     )

       return await get_object_or_404(
            self.session,
            where_attr=AgentStorefront.agent_id,
            where_value=current_user.id
        )
    

    @api_router.get("/storefronts/{slug}")
    async def get_storefront_with_slug(self, slug: str, current_user: CurrentUser):
        # if current_user.role is UserRole.REGULAR:
        #     raise HTTPException(
        #         401
        #     )

       return await get_object_or_404(
            self.session,
            where_attr=AgentStorefront.slug,
            where_value=slug
        )
    

    @api_router.put("/storefronts")
    async def update_store_front(self, body: AgentStorefrontUpdate, current_user: CurrentUser):
        # if current_user.role is UserRole.REGULAR:
        #     raise HTTPException(
        #         401
        #     )

        storefront = await get_object_or_404(
            self.session,
            where_attr=AgentStorefront.agent_id,
            where_value=current_user.id
        )
      
        return await update_object(
            self.session,
            body.model_dump(exclude_unset=True),
            storefront
        )
        
        
        
      
    
    @api_router.post("/utils/create-slug")
    async def create_slug(self, name: str, current_user: CurrentUser):
        return await generate_slug_from_name(self.session, name)


    @api_router.post('/networks')
    async def create_network(self, current_user: CurrentUser, network_data: NetworkCreate):
        if current_user.role is not UserRole.ADMIN: 
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
            model=Network,
            
        )
    
    @api_router.get("/creator/plans/{network_id}")
    async def read_plans(self, current_user: CurrentUser, network_id: str):

        res = await get_objects(
            self.session,
            model=BundlePlan,
            filter_by=(BundlePlan.network_id, network_id)
        )

        needed_plans = []
        for plan in res:
            if plan.creator_id == current_user.id:
                needed_plans.append(plan)
        
        return needed_plans


    
    @api_router.get("/system/plans/{network_id}")
    async def read_network_plans(self, network_id: str, audience: str | None = None):
        admin = await get_object_or_404(
            self.session,
            where_attr=User.role,
            where_value="admin"
        )

        res = await get_objects(
            self.session,
            model=BundlePlan,
            filter_by=(BundlePlan.network_id, network_id)
        )

        if not audience: 
            return res

        needed_plans = []
        for bundle_plan in res:
            if (bundle_plan.audience == audience) and (bundle_plan.creator_id == admin.id):
                needed_plans.append(bundle_plan)

        return needed_plans
    

    @api_router.patch("/update-payment-request/{payment_request_id}")
    async def update_payment_request(self, current_user: CurrentUser, body: UpdatePaymentRequest, payment_request_id: str):
        req = await get_object_or_404(
            self.session,
            where_attr=PaymentRequest.id,
            where_value=payment_request_id
        )

        return await update_object(self.session, body.model_dump(exclude_unset=True), req)
    
    @api_router.delete("/delete-payment-request/{payment_request_id}")
    async def delete_payment_request(self, current_user: CurrentUser, payment_request_id: str):
        req = await get_object_or_404(
            self.session,
            where_attr=PaymentRequest.id,
            where_value=payment_request_id
        )

        await delete(self.session, req)



    @api_router.patch("/plans/{plan_id}")
    async def updated_orders(self, current_user: CurrentUser, body: BundlePlanUpdate , plan_id: str):
        plan = await get_object_or_404(
            self.session,
            where_attr=BundlePlan.id,
            where_value=plan_id
        )
      
        return await update_object(
            self.session,
            body.model_dump(exclude_unset=True),
            plan
        )
    
    @api_router.get('/users/search')
    async def search_users(self, current_user: CurrentUser, email: str):
        return await get_object_or_404(
            self.session,
            where_attr=User.email,
            where_value=email
        )
    
    @api_router.get("/agents/earned/{agent_id}")
    async def get_earned(self, current_user: CurrentUser, agent_id: str):
        orders = await get_objects_v2(
            self.session,
            model=Order,
            where_clauses=[Order.agent_id == agent_id, Order.status == "delivered"]
        )

        return orders

    @api_router.patch("/admin/update-user/{email}")
    async def update_user(self, current_user: CurrentUser, body: UserUpdate, email: str):
        user = await get_object_or_404(
            self.session,
            where_attr=User.email,
            where_value=email
        )

        user = await update_object(
            self.session,
            body.model_dump(exclude_unset=True),
            user
        )

        return UserPublic(**(user.model_dump()))


    
    @api_router.patch("admin/update-user-wallet")
    async def update_user_wallet(self, current_user: CurrentUser, body: WalletUpdate):
        user = await get_object_or_404(
            self.session,
            where_attr=User.email,
            where_value=body.email
        )

        wallet = await get_object_or_404(
            self.session,
            where_attr=Wallet.user_id,
            where_value=user.id
        )

        wallet.balance = Decimal(body.new_balance)
        wallet = await save(self.session, wallet)

        return wallet.balance
    

    @api_router.get("/admin/get-users")
    async def get_users(self, current_user: CurrentUser):
        if current_user.role != "admin":
            raise HTTPException(
                401,
                "Unauthorized Access"
            )
        
        users = await get_objects_v2(
            self.session,
            model=User,
            where_clauses=[User.role != "admin"]
        )

        user_publics = []
        for user in users:
            user_public = UserPublic(
            id=user.id,
            role=user.role,
            email=user.email,
            is_active=user.is_active,
            created_at=user.created_at,
            profile=None

        )   
            user_publics.append(user_public)
        
        return user_publics
            

            






    
    # @api_router.get("/orders")
    # async def read_orders(self, current_user: CurrentUser):
    #     orders = await get_objects_v2(
    #               session=self.session,
    #               model=Order,
    #               options=[selectinload(Order.plan)]  # This will eager load the plan relationship
    #   )
    #     return [OrderRead.model_validate(o) for o in orders]
    

    # @api_router.patch("/orders/{order_id}")
    # async def updated_orders(self, current_user: CurrentUser, body: OrderUpdate, order_id: str):
    #     order = await get_object_or_404(
    #         self.session,
    #         where_attr=Order.id,
    #         where_value=order_id
    #     )
    #     return await update_object(
    #         self.session,
    #         body.model_dump(exclude_unset=True),
    #         order
    #     )
    
    # @api_router.delete("/management/orders/{order_id}")
    # async def delete_order(self, current_user: CurrentUser, order_id: str):
    #     order_db = await get_object_or_404(
    #         self.session,
    #         where_attr=Order.id,
    #         where_value=order_id, 
    #     )
    #     await delete(self.session, order_db)
        

