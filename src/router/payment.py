from fastapi_utils.cbv import cbv
from fastapi import APIRouter, status, Response, Request
from fastapi.exceptions import HTTPException


from src.models.data import UserCreate, EmailUserLogin, UserPublic, InitializePayment
from src.utils.database import get_object_or_404, save
from src.utils.helpers import get_hash, verify_hash, set_del_auth_credentials, make_request
from src.base_router import BaseRouter
from src.models.schemas import User, Order
from src.api.deps import CurrentUser


api_router = APIRouter()


@cbv(api_router)
class PaymentRouter(BaseRouter):
    @api_router.post('/initialize')
    async def initialize(self, payment_data: InitializePayment, current_user: CurrentUser):
        response = make_request(
            "POST", 
            "https://api.paystack.co/transaction/initialize",
             headers={
                "Authorization": "Bearer sk_test_96ab3c5095600279d02b14295b3ecb7a36fe33cd"
             },
            json={
                "email": payment_data.email,
                "amount": str(float(payment_data.amount) * 100),
                "metadata": {
                    "charge_for": payment_data.payment_for,
                    "user_internal_id": current_user.id,
                    "purchase_info": payment_data.purchase_info.model_dump()
                }
            }
        )

        if response.get("status_code"):
            if response["status_code"] == 200:
                return response['data']
        else:
            raise HTTPException(
                500,
                "Something went wrong. Please try again."
            )
    
    @api_router.post("/verify")
    async def verifyPayments(self, request: Request):
        """
        Webhook endpoint for payment verifications.
        """
        response = await request.json()
        if response.get("event"):
            if response["event"] == "charge.success":
                payment_data = response["data"]
                metadata = payment_data["metadata"]
                if metadata.get("charge_for") == "agent-reg":
                    # Make user an agent
                    user_id = metadata["user_internal_id"]
                    user = await get_object_or_404(
                        self.session,
                        where_attr=User.id,
                        where_value=user_id,
                        res=False
                    )
                    user.user_type = 'agent'
                    await save(self.session, user)
                
                if metadata.get("charge_for") == "purchase":
                    user_id = metadata["user_internal_id"]
                    purchase_info = metadata["purchase_info"]
                    # Create order on instantgh
                    response = make_request(
                        "POST",
                        "https://instantdatagh.com/api.php/orders",
                        headers={
                            "Content-Type": "application/json", 
                            "x-api-key": "api_4a78faae8724e4aeabcd60e9892caca25cfc2b0e04b733ad10459f62b455366d"
                        },
                        json={
                            "network": purchase_info.network_name,
                            "phone_number": purchase_info.beneficiary_number,
                            "data_amount": purchase_info.data_amount
                        }
                    )
                    
                    if response.get("status_code"):
                        print(response["status_code"])
                        validated_purchase_info = Order.model_validate(purchase_info, update={
                                                                      "customer_id": user_id
                                                         })
                        await save(self.session, validated_purchase_info, False)


        