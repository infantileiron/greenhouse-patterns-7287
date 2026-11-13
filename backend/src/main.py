import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI,Depends
from fastapi.middleware.cors import CORSMiddleware
from src.config.database import initialize,connect,execute,all_records
from src.config.settings import SEED_DEMO,QUEUE_MODE
from src.middlewares.audit import AuditMiddleware
from src.middlewares.errors import ErrorMiddleware
from src.utils.security import admin
from src.utils.redis_queue import command
from src.routes import auth,datasets,studies,runs,reviews,reports
@asynccontextmanager
async def lifespan(app):
    initialize()
    if SEED_DEMO:
        try:
            from scripts.seed_demo import seed
            seed()
        except Exception: logging.exception('Seed failed; API remains available')
    yield
app=FastAPI(title='南岭温室 · 病征组合筛查',lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=['http://localhost:18204','http://127.0.0.1:18204'],allow_methods=['*'],allow_headers=['*'])
app.add_middleware(AuditMiddleware)
app.add_middleware(ErrorMiddleware)
for module in (auth,datasets,studies,runs,reviews,reports): app.include_router(module.router)
@app.get('/health')
def health():
    with connect() as db: execute(db,'SELECT 1')
    if QUEUE_MODE=='redis': command('PING')
    return {'status':'ok','queue':QUEUE_MODE}
@app.get('/audit')
def audit(user=Depends(admin)): return all_records('audit')[:200]
