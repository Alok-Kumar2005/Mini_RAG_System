from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError, jwt
from src.backend.database import get_db, User
from src.backend.users.controller import hash_password, verify_password, get_current_user, create_access_token
from src.backend.users.schemas import RegisterRequest, LoginResponse, UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register", response_model= UserOut, status_code= status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == body.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code= 400, detail= "Username already exists")
    user = User(username=body.username, hashed_password=hash_password(body.password))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@router.post('/login', response_model= LoginResponse)
async def login(body: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == body.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code= status.HTTP_401_UNAUTHORIZED, detail= "Incorrect username or password")
    
    # token = jwt.encode({'sub': user.id, 'exp': 30})
    token = create_access_token({"sub": user.id})
    return LoginResponse(access_token=token)

@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    return current_user