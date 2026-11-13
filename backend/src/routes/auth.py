from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel,Field
from src.config.database import all_records
from src.utils.security import verify_password,issue_token,current_user
router=APIRouter(prefix='/auth',tags=['auth'])
class Login(BaseModel):
    email: str=Field(max_length=200)
    password: str=Field(max_length=200)
@router.post('/login')
def login(payload:Login):
    user=next((u for u in all_records('users') if u['email']==payload.email),None)
    if not user or not verify_password(payload.password,user['password']): raise HTTPException(401,'邮箱或密码错误')
    return {'token':issue_token(user),'user':{k:v for k,v in user.items() if k!='password'}}
@router.get('/me')
def me(user=Depends(current_user)): return user
