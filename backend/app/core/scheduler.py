"""
Background task scheduler for PRS (every 14 days) and Resilience (every 30 days) calculation.
Uses APScheduler for scheduling periodic jobs.
"""

import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from database import engine, SessionLocal
from repo.repositories import UserRepository, TransactionRepository, SavingRepository, SubscriptionRepository
from business_logic.financial_preference import PeriodicRegretScore

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler: AsyncIOScheduler | None = None


async def calculate_and_save_prs_for_all_users():
    """Calculate PRS for all users every 14 days"""
    logger.info(f"[{datetime.now()}] Starting PRS calculation for all users...")
    
    async with SessionLocal() as db_session:
        try:
            # Get all users
            user_repo = UserRepository(db_session)
            transaction_repo = TransactionRepository(db_session)
            saving_repo = SavingRepository(db_session)
            subscription_repo = SubscriptionRepository(db_session)
            
            # Query all users
            from sqlalchemy import select
            import models
            result = await db_session.execute(select(models.User))
            all_users = result.scalars().all()
            
            for user in all_users:
                try:
                    logger.info(f"Calculating PRS for user {user.id} ({user.username})")
                    
                    # Calculate PRS
                    prs_calculator = PeriodicRegretScore(
                        transaction_repo=transaction_repo,
                        user_repo=user_repo,
                        saving_repo=saving_repo,
                        subscription_repo=subscription_repo,
                    )
                    
                    prs_result = await prs_calculator.to_prs(user.id, lookback_days=14)
                    prs_score = prs_result.get("result", 0.0)
                    
                    # Save PRS to database
                    await user_repo.update_prs(user.id, float(prs_score))
                    logger.info(f"✓ PRS saved for user {user.id}: {prs_score:.4f}")
                    
                except Exception as e:
                    logger.error(f"✗ Error calculating PRS for user {user.id}: {str(e)}")
                    continue
            
            logger.info("✓ PRS calculation completed for all users")
            
        except Exception as e:
            logger.error(f"✗ Error in calculate_and_save_prs_for_all_users: {str(e)}")


async def calculate_and_save_resilience_for_all_users():
    """Calculate Resilience for all users every 30 days"""
    logger.info(f"[{datetime.now()}] Starting Resilience calculation for all users...")
    
    async with SessionLocal() as db_session:
        try:
            # Get all users
            user_repo = UserRepository(db_session)
            transaction_repo = TransactionRepository(db_session)
            saving_repo = SavingRepository(db_session)
            subscription_repo = SubscriptionRepository(db_session)
            
            # Query all users
            from sqlalchemy import select
            import models
            result = await db_session.execute(select(models.User))
            all_users = result.scalars().all()
            
            for user in all_users:
                try:
                    logger.info(f"Calculating Resilience for user {user.id} ({user.username})")
                    
                    # Calculate Resilience
                    resilience_calculator = PeriodicRegretScore(
                        transaction_repo=transaction_repo,
                        user_repo=user_repo,
                        saving_repo=saving_repo,
                        subscription_repo=subscription_repo,
                    )
                    
                    resilience_result = await resilience_calculator.to_resilience(user.id, months=4)
                    resilience_score = resilience_result.get("result", 0.0)
                    
                    # Save Resilience to database
                    await user_repo.update_resilience(user.id, float(resilience_score))
                    logger.info(f"✓ Resilience saved for user {user.id}: {resilience_score:.4f}")
                    
                except Exception as e:
                    logger.error(f"✗ Error calculating Resilience for user {user.id}: {str(e)}")
                    continue
            
            logger.info("✓ Resilience calculation completed for all users")
            
        except Exception as e:
            logger.error(f"✗ Error in calculate_and_save_resilience_for_all_users: {str(e)}")


async def start_scheduler():
    """Initialize and start the APScheduler"""
    global scheduler
    
    if scheduler is not None:
        logger.warning("Scheduler already started")
        return
    
    scheduler = AsyncIOScheduler()
    
    # Schedule PRS calculation every 14 days
    scheduler.add_job(
        calculate_and_save_prs_for_all_users,
        trigger=IntervalTrigger(days=14),
        id="prs_calculation",
        name="PRS Calculation (Every 14 days)",
        replace_existing=True,
        max_instances=1,  # Only one instance at a time
    )
    logger.info("✓ PRS scheduler scheduled: every 14 days")
    
    # Schedule Resilience calculation every 30 days
    scheduler.add_job(
        calculate_and_save_resilience_for_all_users,
        trigger=IntervalTrigger(days=30),
        id="resilience_calculation",
        name="Resilience Calculation (Every 30 days)",
        replace_existing=True,
        max_instances=1,  # Only one instance at a time
    )
    logger.info("✓ Resilience scheduler scheduled: every 30 days")
    
    scheduler.start()
    logger.info("✓ Scheduler started successfully")


async def stop_scheduler():
    """Stop the scheduler gracefully"""
    global scheduler
    
    if scheduler is None:
        logger.warning("Scheduler is not running")
        return
    
    scheduler.shutdown(wait=True)
    scheduler = None
    logger.info("✓ Scheduler stopped")
