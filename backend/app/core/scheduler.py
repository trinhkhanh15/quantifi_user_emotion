from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import date
from schemas.transaction import CreateTransaction
from core.log.logging_activity import log_activity
from business_logic.financial_preference import FinancialPreferenceAnalyzer
from repo.repositories import UserRepository, SavingRepository, SubscriptionRepository, TransactionRepository
from database import AsyncSessionLocal
from sqlalchemy import select
import models

scheduler = AsyncIOScheduler()


async def _30d_job(user_id: int,
                    user_repo: UserRepository,
                    saving_repo: SavingRepository,
                    subscription_repo: SubscriptionRepository,
                    transaction_repo: TransactionRepository):
    try:
        today = date.today()
        begin_this_month = date(today.year, today.month, 1)
        
        monthly_income = await transaction_repo.get_monthly_income(user_id, begin_this_month, today)
        await user_repo.update_monthly_income(user_id, monthly_income)

        analyzer = FinancialPreferenceAnalyzer(user_repo, transaction_repo, subscription_repo, saving_repo)
        rs = (await analyzer.to_resilience(user_id)).get("final_score")
        await user_repo.update_resilience(user_id, rs)

        msg = f"Update monthly income and resilience score for user ID={user_id} sucessfully."
        log_activity(msg, "info")
    except ValueError as e:
        msg = f"Update monthly income and resilience score for user ID={user_id} failed."
        log_activity(msg, "error")

async def _14d_job(user_id: int, 
                    user_repo: UserRepository,
                    saving_repo: SavingRepository,
                    subscription_repo: SubscriptionRepository,
                    transaction_repo: TransactionRepository):
    try:
        analyzer = FinancialPreferenceAnalyzer(user_repo, transaction_repo, subscription_repo, saving_repo)
        prs = (await analyzer.to_prs(user_id)).get("final_score")
        await user_repo.update_prs(user_id, prs)

        msg = f"Update PRS for user ID={user_id} sucessfully."
        log_activity(msg, "info")
    except ValueError as e:
        msg = f"Update PRS for user ID={user_id} failed."
        log_activity(msg, "error")

        
async def _run_prs_for_all_users():
    """Create repos per-session and run PRS job for every user."""
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        transaction_repo = TransactionRepository(session)
        saving_repo = SavingRepository(session)
        subscription_repo = SubscriptionRepository(session)

        result = await session.execute(select(models.User))
        users = result.scalars().all()

        for u in users:
            try:
                await _14d_job(u.id, user_repo, saving_repo, subscription_repo, transaction_repo)
            except Exception as e:
                log_activity(f"PRS job failed for user {u.id}: {e}", "error")


async def _run_resilience_for_all_users():
    """Create repos per-session and run Resilience job for every user."""
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        transaction_repo = TransactionRepository(session)
        saving_repo = SavingRepository(session)
        subscription_repo = SubscriptionRepository(session)

        result = await session.execute(select(models.User))
        users = result.scalars().all()

        for u in users:
            try:
                await _30d_job(u.id, user_repo, saving_repo, subscription_repo, transaction_repo)
            except Exception as e:
                log_activity(f"Resilience job failed for user {u.id}: {e}", "error")


def start_scheduler():
    """Schedule monthly jobs (14th and 30th) that iterate all users.

    Note: This function starts the global scheduler and must be called once on
    application startup.
    """
    _14d_trigger = CronTrigger(day="14", hour=0, minute=0)
    _30d_trigger = CronTrigger(day="30", hour=0, minute=0)

    # Schedule callable coroutines (APScheduler will call these functions)
    scheduler.add_job(
        _run_prs_for_all_users,
        trigger=_14d_trigger,
        id="14days_job",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
    )
    scheduler.add_job(
        _run_resilience_for_all_users,
        trigger=_30d_trigger,
        id="30days_job",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
    )

    scheduler.start()


def stop_scheduler():
    try:
        scheduler.shutdown(wait=False)
    except Exception:
        pass
    
