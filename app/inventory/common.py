import logging
import os

from logging.handlers import RotatingFileHandler

import jwt
from fastapi_cache import caches
from fastapi_cache.backends.redis import CACHE_KEY, RedisCacheBackend
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings
from app.inventory.schemas import UserInfo

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler(
    os.path.join(settings.LOG_PATH, 'app.log'),
    maxBytes=50000,
    backupCount=1
)
logger.addHandler(handler)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)

security_scheme = HTTPBearer(
    bearerFormat="JWT",
    scheme_name="JWT Auth",
    description="Введите ваш JWT токен в формате: Bearer <token>"
)


async def get_current_user(
    authorization: HTTPAuthorizationCredentials = Depends(security_scheme)
) -> UserInfo:
    token = authorization.credentials
    try:
        decoded = jwt.decode(token, options={'verify_signature': False})
        user_id = decoded.get('user_id', None)
        if not user_id:
            user_id = int(decoded.get('sub'))
        role = decoded.get('role')
        if not user_id or not role:
            raise HTTPException(
                detail='Token must contains user_id and role',
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        return UserInfo(user_id=user_id, role=role)
    except jwt.InvalidTokenError:
        raise HTTPException(
            detail='Wrong token',
            status_code=status.HTTP_401_UNAUTHORIZED
        )


async def redis_cache():
    return caches.get(CACHE_KEY)


async def get_cache() -> RedisCacheBackend | None:
    return await redis_cache()
