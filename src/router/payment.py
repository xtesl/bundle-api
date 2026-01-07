from fastapi_utils.cbv import cbv
from fastapi import APIRouter, status, Response, Request, BackgroundTasks
from fastapi.exceptions import HTTPException
from decimal import Decimal


from src.models.data import InitializePayment, BuyBundle, CreatePaymentRequest, BuyBundleFromAgent
from src.utils.database import get_object_or_404, save, get_objects
from src.utils.helpers import make_request
from src.base_router import BaseRouter
from src.models.schemas import User, Order, Wallet, BundlePlan, PaymentRequest, Transaction
from src.api.deps import CurrentUser


api_router = APIRouter()

async def save_model(session, model):
    await save(session, model)

@cbv(api_router)
class PaymentRouter(BaseRouter):
    @api_router.post("/create-payment-request")
    async def create_payment_request(self, data: CreatePaymentRequest, current_user: CurrentUser):
        if current_user.role != 'agent':
            raise HTTPException(
                401,
                "Unathorized Acess"
            )

        req = PaymentRequest(
            agent_id=current_user.id,
            email=current_user.email,
            amount=Decimal(data.amount),
            mobilemoney_name=data.mobilemoney_name,
            receiver_number=data.receiver_number,
            status="pending"
        )

        return await save(self.session, req, True)
    
    @api_router.get("/payment-requests")
    async def get_requests(self, current_user: CurrentUser):
        if current_user.role != "admin":
            raise HTTPException(
                401,
                "Unathorized Access"
            )
        
        return await get_objects(
            self.session,
            model=PaymentRequest,
        )
    
    @api_router.get("/payment-requests/me")
    async def get_my_requests(self, current_user: CurrentUser):
        if current_user.role != "agent":
            raise HTTPException(
                401,
                "Unathorized Access"
            )
        
        return await get_objects(
            self.session,
            model=PaymentRequest,
            filter_by=(PaymentRequest.agent_id, current_user.id)
        )
    

    @api_router.post('/initialize-agent-purchase')
    async def initialize_agent_purchase(self, data: BuyBundleFromAgent, current_user: CurrentUser):

        plan = await get_object_or_404(
            self.session,
            where_attr=BundlePlan.id,
            where_value=data.plan_id
        )

        agent_wallet = await get_object_or_404(
            self.session,
            where_attr=Wallet.user_id,
            where_value=plan.agent_id
        )

        if agent_wallet.balance < plan.base_price:
            raise HTTPException(
                402,
                "Service Unavailable"
            )

        transaction = Transaction(
                amount=plan.base_price,
                user_id=current_user.id,
                transaction_type='purchase',
                status="incomplete"
        )
        transaction =await save(self.session, transaction, True)
      

        response = make_request(
            "POST", 
            "https://api.paystack.co/transaction/initialize",
             headers={
                "Authorization": "Bearer sk_live_28ba29a72a3feec4da308f4155cb8611f19f901f"
             },
            json={
                "email": current_user.email,
                "amount": str(float(plan.base_price) * 100),
                "metadata": {
                    "charge_for": data.payment_for,
                    "user_internal_id": current_user.id,
                    "agent_id": plan.creator_id,
                    "beneficiary_number": data.beneficiary_number,
                    "package_size": plan.value,
                    "plan_id": plan.id,
                    "price_paid": str(plan.base_price),
                    "transaction_id": transaction.id
                }
            }
        )

        # print(response)
        if response.get("status_code"):
            if response["status_code"] == 200:
                return response['data']
        else:
            raise HTTPException(
                500,
                "Something went wrong. Please try again."
            )


    @api_router.post("/buy-bundle")
    async def buy(self, current_user: CurrentUser, data: BuyBundle, background_tasks: BackgroundTasks):
        wallet = await get_object_or_404(
            self.session,
            where_attr=Wallet.user_id,
            where_value=current_user.id,
            res=False
        )

        plan = await get_object_or_404(
            self.session,
            where_attr=BundlePlan.id, 
            where_value=data.plan_id
        )

        if wallet.balance < plan.base_price:
            raise HTTPException(
                402,
                "Insufficient wallet balance. Please top up your wallet."
            )
        

        res = make_request(
                        "POST",
                        "https://www.blessdatahub.com/api/create_order.php",
                        headers={
                            "Content-Type": "application/json", 
                            "Authorization": "Bearer XUBeGct8zRgnaqMmlmGxZBOZ1zmKVHeI"
                        },
                        json=
                           {
                       "beneficiary": data.beneficiary_number,
                       "package_size": data.package_size
                       }
                        
                    )


       

        if res.get("status_code"):
            if res["status_code"] == 201:
                data = res["data"]["data"]
                external_id = data["api_results"][0]["order_id"] 
                status = data["api_results"][0]["status"] 
                order = Order(
                    user_id=current_user.id,
                    plan_id=plan.id,
                    beneficiary_number=data.beneficiary_number,
                    price_paid=plan.base_price,
                    external_id=external_id,
                    status=status
                )

                order = await save(self.session, order, True)
                wallet.balance = wallet.balance - plan.base_price
                await save(self.session, wallet)

                transaction = Transaction(
                    amount=plan.base_price,
                    transaction_type='purchase'
                )
                background_tasks.add_task(save_model, self.session, transaction)

                return order

            elif res["status_code"] == 402:
                raise HTTPException(
                    503,
                    "Service Unavailable"
                )
            else:
                raise HTTPException(
                500,
                "Something went wrong. Please try again or contact support."
            )
            
        
        else:
            raise HTTPException(
                500,
                "Something went wrong. Please try again or contact support."
            )
        

    
    @api_router.get("/transactions/me")
    async def get_transactions(self, current_user: CurrentUser):
        return await get_objects(
            self.session,
            model=Transaction,
            filter_by=(Transaction.user_id, current_user.id)
        )

       

    @api_router.post('/initialize')
    async def initialize(self, payment_data: InitializePayment, current_user: CurrentUser):
        response = make_request(
            "POST", 
            "https://api.paystack.co/transaction/initialize",
             headers={
                "Authorization": "Bearer sk_live_28ba29a72a3feec4da308f4155cb8611f19f901f"
             },
            json={
                "email": current_user.email,
                "amount": str(float(payment_data.amount) * 100),
                "metadata": {
                    "charge_for": payment_data.payment_for,
                    "user_internal_id": current_user.id
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
    async def verifyPayments(self, request: Request, background_tasks: BackgroundTasks):
        """
        Webhook endpoint for payment verifications.
        """
        response = await request.json()
        if response.get("event"):
            if response["event"] == "charge.success":
                payment_data = response["data"]
                metadata = payment_data["metadata"]
                if metadata.get("charge_for") == "topup":
                    # Make user an agent
                    user_id = metadata["user_internal_id"]
                    wallet = await get_object_or_404(
                        self.session,
                        where_attr=Wallet.user_id,
                        where_value=user_id,
                        res=False
                    )

                    

                    transaction = Transaction(
                        amount=(Decimal(str(payment_data["amount"])) / 100) ,
                        transaction_type='topup',
                        user_id=user_id,
                        reference=payment_data["reference"]
                     )

                    background_tasks.add_task(save_model, self.session, transaction)

                    wallet.balance = wallet.balance + (Decimal(str(payment_data["amount"])) / 100)
                    await save(self.session, wallet)

                
                if metadata.get("charge_for") == "agent_reg":
                    user_id = metadata["user_internal_id"]
                    user = await get_object_or_404(
                        self.session,
                        where_attr=User.id,
                        where_value=user_id,
                        res=False
                    )

                    transaction = Transaction(
                        amount=(Decimal(str(payment_data["amount"])) / 100) ,
                        transaction_type='purchase',
                        user_id=user_id,
                        reference=payment_data["reference"]
                     )

                    background_tasks.add_task(save_model, self.session, transaction)


                    user.role = "agent"
                    await save(self.session, user)
            

                if metadata.get("charge_for") == "buy-bundle":
                    user_id = metadata["user_internal_id"]
                    package_size = metadata["package_size"]
                    beneficiary_number = metadata["beneficiary_number"]
                    plan_id = metadata["plan_id"]
                    base_price = metadata["price_paid"]
                    agent_id = metadata["agent_id"]

                    trns = await get_object_or_404(
                        self.session,
                        where_attr=Transaction.id,
                        where_value=metadata["transaction_id"]
                    )
                    trns.status = 'complete'

                    background_tasks.add_task(save_model, self.session, trns)
                    
                    res = make_request(
                        "POST",
                        "https://www.blessdatahub.com/api/create_order.php",
                        headers={
                            "Content-Type": "application/json", 
                            "Authorization": "Bearer XUBeGct8zRgnaqMmlmGxZBOZ1zmKVHeI"
                        },
                        json=
                           {
                       "beneficiary": beneficiary_number,
                       "package_size": package_size
                       }
                        
                    )

                    # print(res)
                    

                    if res.get("status_code"):
                        if res["status_code"] == 201:
                            data = res["data"]["data"]
                            external_id = data["api_results"][0]["order_id"] 
                            status = data["api_results"][0]["status"] 
                            order = Order(
                                 user_id=user_id,
                                 plan_id=plan_id,
                                 agent_id=agent_id,
                                 beneficiary_number=beneficiary_number,
                                 price_paid=base_price,
                                 external_id=external_id,
                                 status=status
                            )

                            agent_wallet = get_object_or_404(
                                self.session,
                                where_attr=Wallet.id,
                                where_value=agent_id
                            )
                            agent_wallet.balance = agent_wallet.balance - Decimal(base_price)

                            background_tasks.add_task(save_model, self.session, agent_wallet)
                            
                            await save(self.session, order, True)
                            
                    

                            

                        

                        
            
            
        
        


                
                        
                    
                    
                    
           