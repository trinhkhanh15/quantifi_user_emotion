from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware # Thêm dòng này
from routers import user, saving, transaction, subscription, chatbot
from contextlib import asynccontextmanager
from repo.repositories import init_db
import logging
from typing import Annotated

from repo.repositories import UserRepository, TransactionRepository, SavingRepository, SubscriptionRepository
from dependancies.injection import get_saving_repo, get_user_repo, get_transaction_repo, get_subscription_repo
from schemas import user as sche_user
from business_logic.subscription import check_billing_date
from core.security.token import get_current_user
from core.scheduler import start_scheduler, stop_scheduler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(lifespan=lifespan)

# --- THÊM ĐOẠN NÀY VÀO ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Cho phép tất cả các nguồn (đúng chất vibe code)
    allow_credentials=True,
    allow_methods=["*"], # Cho phép tất cả các method (GET, POST, OPTIONS...)
    allow_headers=["*"], # Cho phép tất cả các headers
)
# -------------------------

# Lưu ý: Các dòng include_router phải nằm DƯỚI đoạn add_middleware
app.include_router(user.router, tags=["user"], prefix="/user")
app.include_router(saving.router, tags=["saving"], prefix="/saving")
app.include_router(transaction.router, tags=["transaction"], prefix="/transaction")
app.include_router(subscription.router, tags=["subscription"], prefix="/subscription")
app.include_router(chatbot.router, tags=["chatbot"], prefix="/chatbot")

@app.on_event("startup")
async def startup_event():
    # Start background scheduler (schedules jobs that iterate all users)
    start_scheduler()


@app.on_event("shutdown")
async def shutdown_event():
    # Stop scheduler gracefully
    try:
        stop_scheduler()
    except Exception:
        pass

@app.get("/")
async def root():
    return {"detail": "Personal Finance Assistant"}