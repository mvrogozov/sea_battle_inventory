import logging
import os
import jwt

from typing import Annotated
from logging.handlers import RotatingFileHandler

from fastapi import Header, HTTPException, status

from app.inventory.schemas import UserInfo
from app.config import settings


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


async def get_current_user(
        authorization: Annotated[str | None, Header()] = None
) -> UserInfo:
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(
            detail='Needs Bearer token',
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    token = authorization[7:]
    try:
        decoded = jwt.decode(token, options={'verify_signature': False})
        user_id = decoded.get('user_id')
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
