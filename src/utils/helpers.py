from sqlmodel.ext.asyncio.session import AsyncSession
from datetime import datetime, timezone, timedelta
import requests
from typing import Any, Optional, Dict, Literal
import os
from dotenv import load_dotenv
from passlib.context import CryptContext
from jose import jwt, JWTError
from fastapi import Response
import re
from sqlmodel import select
from unidecode import unidecode 
from src.models.schemas import AgentStorefront


load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"
SECRET_KEY = os.getenv('SECRET_KEY')
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES')
REFRESH_TOKEN_EXPIRE_MINUTES = os.getenv('REFRESH_TOKEN_EXPIRE_MINUTES')
PROJECT_NAME = os.getenv('PROJECT_NAME')






def create_jwt_token(subject: Any, expires_timedelta: timedelta) -> str:
    expires_at = datetime.now(timezone.utc) + expires_timedelta
    to_encode = {"sub": subject, "exp": expires_at}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, ALGORITHM)
    return encoded_jwt


def create_auth_token(subject: str | Any, expires_delta: timedelta, type: Literal["access", "refresh"]) -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"exp": expire, "sub": str(subject), "token_type": type}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_jwt(token: str) -> Any:
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def set_del_auth_credentials(
    response: Response,
    token_type: Literal["access", "refresh"],
    operation: Literal["set", "delete"] = "set",
    token_data: str | None = None,
    ) -> None:
    """
    Generates and sets authentication tokens as HTTP-Only cookies.
    
    Can also be used for logout process, where you need to delete
    authentication credentials.
    
    Args:
      token_type: Authentication token type (`access_token`, `refresh_token`).When wrong type is 
                  passed, `access_token` type will be used.
      
      response: The HTTP response object to set the cookies on.
      
      token_data: User's data to be used for the JWT token generation i.e sub
      
      operation: Operation to be performed, to delete token or set token.
      returns: `None`
    """
    # Delete token
    if operation == "delete":
        response.delete_cookie(
            key=token_type,
            httponly=True,
        )
        return
        
    # Tokens expire times
    access_token_expires = timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
    refresh_token_expires = timedelta(minutes=int(REFRESH_TOKEN_EXPIRE_MINUTES))
      
    expire_times_delta = {
          "access": access_token_expires,
          "refresh": refresh_token_expires
        }
    expire_times = {
        "access": int(ACCESS_TOKEN_EXPIRE_MINUTES) * 60,
        "refresh": int(ACCESS_TOKEN_EXPIRE_MINUTES) * 60
    }
    
    
    # Select token expiration time delta
    expire_time_delta = expire_times_delta[token_type]

    # Select cookie expiration time in seconds
    expire_time = expire_times[token_type]
    
    token = create_auth_token(
                token_data,
                expire_time_delta,
                type=token_type,
            )
    
    cookie_key = (
         f"{PROJECT_NAME.lower()}-access-token" if token_type == 'access'
         else f"{PROJECT_NAME.lower()}-refresh-token"
    )

    response.set_cookie(
        key=cookie_key,
        value=token,
        httponly=True,
        samesite="none",
        secure=True,
        max_age=expire_time # Convert from minutes to seconds
    )



def make_request(
    method: str,
    url: str,
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    json: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
) -> Any:
    """
    Makes an HTTP request.
    
    Args:
       method: HTTP method(GET, PUT, POST, DELETE, etc.).
       url: Full URL of the endpoint.
       params: Query parameters for GET requests.
       data: Form data for POST/PUT requests.
       json: JSON data for POST/PUT requests.
       headers: Additional HTTP headers.
    
    Returns:
        Parsed JSON response or raw text.
    """
    response = None  # Initialize response here
    
    try:
        response = requests.request(
            method, url,
            params=params, data=data,
            json=json, headers=headers
        )
        
        response.raise_for_status()
        return {
            "data": response.json(),
            "status_code": response.status_code
        }
    
    except requests.exceptions.HTTPError as e:
        # response is guaranteed to exist here because HTTPError only happens after request
        return {
            "HTTP_ERROR": True,
            "status_code": response.status_code,
            "data": response.json() if response else None
        }
    
    except requests.exceptions.JSONDecodeError:
        # response exists but JSON parsing failed
        return {
            "HTTP_ERROR": True,
            "status_code": response.status_code if response else None
        }
    
    except requests.exceptions.ConnectionError:
        # Connection failed - response doesn't exist
        return {
            "CONNECTION_ERROR": True
        }
    
    except ValueError:
        # Value error - response may or may not exist
        return {
            "PARSE_ERROR": True,
            "status_code": response.status_code if response else None
        }
    
    except Exception as e:
        # Catch any other unexpected errors
        return {
            "ERROR": True,
            "message": str(e),
            "status_code": response.status_code if response else None
        }



def gen_offset_pagination_metadata(offset: int, limit: int, total: int, trailing_url: str) -> dict:
    """
    Generates offset-based pagination metadata for response.
    """
    
    next_offset = offset + limit if (offset + limit) < total else None
    previous_offset = offset - limit if (offset - limit) >= 0 else None
    
    return {
        "total_items": total,
        "limit": limit,
        "offset": offset,
        "next": (
             f"{trailing_url}?limit={limit}&offset={next_offset}"
             if next_offset is not None
             else None
         ),
        "prev": (
            f"{trailing_url}?limit={limit}&offset={previous_offset}"
            if previous_offset is not None
            else None
        )
   }


def load_env_var(var_name: str) -> str:
    """
    Load an environment variable from the .env file.
    """
    load_dotenv()
    value = os.getenv(var_name)
    if value is None:
        raise ValueError(f"Environment variable '{var_name}' not found.")
    return value


def get_hash(raw: str) -> str:
    return pwd_context.hash(raw)

def verify_hash(raw, hash) -> bool: 
    return pwd_context.verify(raw, hash)


 
async def generate_slug_from_name(session: AsyncSession, name: str) -> str:
    """
    Generate a unique URL-safe slug from the agent's name.
    
    Args:
        session: SQLModel AsyncSession
        name: Agent's name or business name
        
    Returns:
        A unique URL-safe slug
        
    Example:
        "John's Data Store" -> "johns-data-store"
        "MTN & Vodafone Hub" -> "mtn-vodafone-hub"
        "Kwame's Shop" -> "kwames-shop"
    """
    # Convert to lowercase and remove accents
    slug = unidecode(name).lower()
    
    # Replace spaces and special characters with hyphens
    slug = re.sub(r'[^\w\s-]', '', slug)  # Remove special chars except spaces and hyphens
    slug = re.sub(r'[-\s]+', '-', slug)    # Replace spaces/multiple hyphens with single hyphen
    
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    
    # Ensure slug is not empty
    if not slug:
        raise ValueError("Cannot generate slug from empty name")
    
    # Check if slug exists and make it unique by appending numbers
    original_slug = slug
    counter = 1
    
    while True:
        # Check if this slug already exists in database
        statement = select(AgentStorefront).where(AgentStorefront.slug == slug)
        result = await session.exec(statement)
        existing = result.first()
        
        if not existing:
            # Slug is unique, we can use it
            break
            
        # Slug exists, try with counter
        slug = f"{original_slug}-{counter}"
        counter += 1
    
    return slug




