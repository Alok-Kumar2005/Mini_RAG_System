from datetime import datetime
from pydantic import BaseModel, Field

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
 
 
class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
 
 
class UserOut(BaseModel):
    id: str
    username: str
    created_at: datetime
 
    model_config = {"from_attributes": True}