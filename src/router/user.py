from fastapi_utils.cbv import cbv
from fastapi import APIRouter, status, Response
from fastapi.exceptions import HTTPException


from src.models.data import UserCreate, EmailUserLogin, UserPublic
from src.utils.database import get_object_or_404, save
from src.utils.helpers import get_hash, verify_hash, set_del_auth_credentials
from src.base_router import BaseRouter
from src.models.schemas import User
from src.api.deps import CurrentUser


api_router = APIRouter()


@cbv(api_router)
class UserRouter(BaseRouter):
    @api_router.post("/auth/signup/email", response_model=UserPublic)
    async def sign_up_email(self, user_data: UserCreate, res: Response):
        # Check for user existence 
        user = await get_object_or_404(
            self.session,
            where_attr=User.email,
            where_value=user_data.email,
            res=False
        )

        if not user:
            validated_user_data = User.model_validate(user_data, update={
                "password_hash": get_hash(user_data.password)
            })

            user_db = await save(self.session, validated_user_data, True)
            set_del_auth_credentials(res, 'access', token_data=user_db.id)
            set_del_auth_credentials(res, 'refresh', token_data=user_db.id)
            return user_db
        
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists."
        )
    
    @api_router.post("/auth/login/email", response_model=UserPublic)
    async def email_login(self, credentials: EmailUserLogin, res: Response):
        user = await get_object_or_404(
            self.session,
            where_attr=User.email,
            where_value=credentials.email,
            res=False
        )
        if user:
            # Authenticate user
            if verify_hash(credentials.password, user.password_hash):
                set_del_auth_credentials(res, 'access', token_data=user.id)
                set_del_auth_credentials(res, 'refresh', token_data=user.id)
                return user
            else:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid credentials."
                )
        raise HTTPException(
            401,
            detail=f"No account is associated with the email {credentials.email}"

        )
    
    @api_router.post("/auth/logout")
    async def logout(self, res: Response):
        set_del_auth_credentials(res, "access", "set", "")
        set_del_auth_credentials(res, "refresh", "set", "")
        res.status_code = 204
    
    @api_router.get("/", response_model=UserPublic)
    async def get_user_data(self, current_user: CurrentUser):
        return current_user



        