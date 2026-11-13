import logging
import time
from starlette.middleware.base import BaseHTTPMiddleware
from src.config.database import save
from src.utils.security import read_token
class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self,request,call_next):
        started=time.monotonic(); response=await call_next(request)
        if request.method not in ('GET','OPTIONS'):
            actor='anonymous'
            try: actor=read_token(request.headers.get('authorization','').split(' ',1)[-1])['email']
            except Exception: pass
            try:
                save('audit',{'actor':actor,'method':request.method,'path':request.url.path,'status':response.status_code,'duration_ms':round((time.monotonic()-started)*1000)})
            except Exception: logging.exception('Audit persistence failed')
        return response
