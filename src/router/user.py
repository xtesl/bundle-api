from fastapi_utils.cbv import cbv
from fastapi import APIRouter, status, Response
from fastapi.exceptions import HTTPException

from src.models.data import UserCreate, EmailUserLogin, UserPublic, WalletRead
from src.utils.database import get_object_or_404, save
from src.utils.helpers import get_hash, verify_hash, set_del_auth_credentials
from src.base_router import BaseRouter
from src.models.schemas import User, UserProfile, Wallet
from src.api.deps import CurrentUser


api_router = APIRouter()


@cbv(api_router)
class UserRouter(BaseRouter):

    @api_router.post("/auth/signup/email", response_model=UserPublic)
    async def sign_up_email(self, user_data: UserCreate, res: Response):
        # Check if user already exists
        user = await get_object_or_404(
            self.session,
            where_attr=User.email,
            where_value=user_data.email,
            res=False
        )

        if user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists."
            )

        # Create user
        user_db = User(
            email=user_data.email,
            password_hash=get_hash(user_data.password)
        )

        user_db = await save(self.session, user_db, refresh=True)

        # Create profile
        profile = UserProfile(
            user_id=user_db.id,
            name=None,
            phone=None
        )
        await save(self.session, profile)

        # Create wallet
        wallet = Wallet(
            user_id=user_db.id,
            balance=0
        )
        await save(self.session, wallet)

        # Set auth cookies
        set_del_auth_credentials(res, "access", token_data=user_db.id)
        set_del_auth_credentials(res, "refresh", token_data=user_db.id)

        return UserPublic(
               id=user_db.id,
               email=user_db.email,
               role=user_db.role,
               is_active=user_db.is_active,
               created_at=user_db.created_at,
               profile=None
        )


    @api_router.post("/auth/login/email", response_model=UserPublic)
    async def email_login(self, credentials: EmailUserLogin, res: Response):
        user = await get_object_or_404(
            self.session,
            where_attr=User.email,
            where_value=credentials.email,
            res=False
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"No account is associated with the email {credentials.email}"
            )

        if not verify_hash(credentials.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials."
            )

        set_del_auth_credentials(res, "access", token_data=user.id)
        set_del_auth_credentials(res, "refresh", token_data=user.id)

        return UserPublic(
               id=user.id,
               email=user.email,
               role=user.role,
               is_active=user.is_active,
               created_at=user.created_at,
               profile=None
        )


    @api_router.post("/auth/logout", status_code=204)
    async def logout(self, res: Response):
        set_del_auth_credentials(res, "access", "set", "")
        set_del_auth_credentials(res, "refresh", "set", "")
    
    @api_router.get("/wallet/read", response_model=WalletRead)
    async def check_balance(self, current_user: CurrentUser):
        wallet = await get_object_or_404(
            self.session,
            where_attr=Wallet.user_id,
            where_value=current_user.id,
            res=False
        )

        return WalletRead(
            balance=wallet.balance
        )

    @api_router.get("/", response_model=UserPublic)
    async def get_user_data(self, current_user: CurrentUser):
         return UserPublic(
               id=current_user.id,
               email=current_user.email,
               role=current_user.role,
               is_active=current_user.is_active,
               created_at=current_user.created_at,
               profile=None
        )
    
    @api_router.get("/upgrade-to-admin")
    async def upgrade_user_to_admin(self, current_user: CurrentUser):
        current_user.role = "admin"
        await save(self.session, current_user)