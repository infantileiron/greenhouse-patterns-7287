import base64
import hashlib
import hmac
import json
import secrets
import time
from fastapi import HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from src.config.settings import JWT_SECRET
from src.constants.enums import Role
from src.config.database import get
bearer = HTTPBearer(auto_error=False)
def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 180000).hex()
    return salt + ':' + digest
def verify_password(password, encoded):
    return hmac.compare_digest(hash_password(password, encoded.split(':')[0]), encoded)
def enc(value):
    return base64.urlsafe_b64encode(value).decode().rstrip('=')
def issue_token(user):
    head = enc(b'{"alg":"HS256","typ":"JWT"}')
    body = enc(json.dumps({'sub':user['id'], 'exp':int(time.time())+28800}).encode())
    sig = enc(hmac.new(JWT_SECRET.encode(), f'{head}.{body}'.encode(), hashlib.sha256).digest())
    return f'{head}.{body}.{sig}'
def read_token(token):
    try:
        head, body, sig = token.split('.')
        header = json.loads(base64.urlsafe_b64decode(head+'='*(-len(head)%4)))
        if header.get('alg') != 'HS256': raise ValueError()
        expected = enc(hmac.new(JWT_SECRET.encode(), f'{head}.{body}'.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(sig, expected): raise ValueError()
        claim = json.loads(base64.urlsafe_b64decode(body+'='*(-len(body)%4)))
        if claim['exp'] <= time.time(): raise ValueError()
        user = get('users', claim['sub'])
        if not user: raise ValueError()
        return {k:v for k,v in user.items() if k != 'password'}
    except Exception:
        raise HTTPException(401, '登录已过期，请重新登录')
def current_user(auth: HTTPAuthorizationCredentials = Depends(bearer)):
    if not auth: raise HTTPException(401, '请先登录')
    return read_token(auth.credentials)
def writer(user=Depends(current_user)):
    if user['role'] not in (Role.ADMIN.value,Role.ANALYST.value): raise HTTPException(403, '观察员不能修改研究')
    return user
def admin(user=Depends(current_user)):
    if user['role'] != Role.ADMIN.value: raise HTTPException(403, '仅管理员可批准复查')
    return user
