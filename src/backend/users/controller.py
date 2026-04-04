import os
from typing import Optional
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.backend.database import get_db, User
from src.utils import utils

pwd_context = CryptContext(schemes=['bcrypt'])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl= '/api/auth/login')

def hash_password(password: str) -> str:
    return pwd_context.hash(password)
 
 
def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, exp_time: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expires_time = datetime.now(timezone.utc) + (exp_time or timedelta(minutes=utils.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expires_time})
    return jwt.encode(to_encode, utils.SECRET_KEY, algorithm= utils.ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db))-> User:
    cred_exception = HTTPException(status_code= status.HTTP_401_UNAUTHORIZED, detail= "Could not validate credentials")
    try:
        payload = jwt.decode(token, utils.SECRET_KEY, algorithms= [utils.ALGORITHM])
        user_id: str = payload.get('sub')
        if user_id is None:
            raise cred_exception
    except JWTError:
        raise cred_exception
    # result = await db.query(User).filter(User.id == user_id)  ## only work for sync
    result = await db.execute(select(User).where(User.id == user_id))  
    user = result.scalar_one_or_none()
    if user is None:
        raise cred_exception
    return user