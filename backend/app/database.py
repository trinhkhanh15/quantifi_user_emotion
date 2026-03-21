from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

import os
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://admin:123@localhost:5432/finance_assistant")

engine = create_async_engine(
    DATABASE_URL,
    echo=True, # Set True nếu muốn xem log SQL chạy dưới console
    future=True
)

Base = declarative_base()

# 3. Cấu hình Session maker
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    class_=AsyncSession,
    expire_on_commit=False,
)