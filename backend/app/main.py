from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # Thêm dòng này
from routers import user, saving, transaction, subscription, chatbot
from contextlib import asynccontextmanager
from repo.repositories import init_db
# from core.scheduler import start_scheduler, stop_scheduler
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    # await start_scheduler()  # Start background tasks on app startup
    # logger.info("✓ Application started with background scheduler")
    yield
    # await stop_scheduler()  # Stop background tasks on app shutdown
    # logger.info("✓ Application shutdown with background scheduler stopped")

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

@app.get("/")
async def root():
    return {"detail": "Personal Finance Assistant"}