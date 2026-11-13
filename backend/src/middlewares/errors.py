import logging
from uuid import uuid4
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
class ErrorMiddleware(BaseHTTPMiddleware):
    async def dispatch(self,request,call_next):
        request_id=str(uuid4())
        try:
            response=await call_next(request)
        except Exception:
            logging.exception('Unhandled request %s',request_id)
            response=JSONResponse({'detail':'处理失败，请重试；若持续失败请提供请求编号','request_id':request_id},status_code=500)
        response.headers['X-Request-ID']=request_id
        return response
