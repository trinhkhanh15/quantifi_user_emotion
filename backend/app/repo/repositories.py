from unicodedata import category
import models
from database import engine
from sqlalchemy import select, func, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from schemas import user as sche_user, saving as sche_saving, transaction as sche_transaction, subscription as sche_subscription
from core.security.encryption import verity_password
from datetime import date, timedelta, datetime
import asyncio

CATEGORY_BUDGET_MAP = {
    "food and drink": "fad_budget",
    "shopping":       "shopping_budget",
    "investment":     "investment_budget",
    "moving":         "moving_budget",
    "entertainment":  "entertainment_budget",
    "other":          "other_budget",
}

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

class BaseRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

class UserRepository(BaseRepository):
    async def update_budget(self, user_id: int, budget_data: sche_user.SetBudget):
        user = await self.get_by_id(user_id)
        if not user:
            return None
        user.fad_budget = budget_data.fad_budget
        user.shopping_budget = budget_data.shopping_budget
        user.investment_budget = budget_data.investment_budget
        user.moving_budget = budget_data.moving_budget
        user.entertainment_budget = budget_data.entertainment_budget
        user.other_budget = budget_data.other_budget
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get_by_id(self, user_id: int):
        user = await self.db.execute(select(models.User).filter(models.User.id == user_id))
        return user.scalars().first()

    async def get_by_name(self, username: str):
        user = await self.db.execute(select(models.User).filter(models.User.username == username))
        return user.scalars().first()

    async def validate_user(self, username: str, password: str):
        user_execute = await self.get_by_name(username)
        if not user_execute:
            return None
        if not verity_password(password, str(user_execute.password)):
            return None
        return True

    async def create(self, user: sche_user.CreateUser):
        # Defensive check to avoid unique constraint violation
        existing = await self.get_by_name(user.username)
        if existing:
            return None

        new_user = models.User(
            username=user.username,
            password=user.password,
            age=user.age,
            sex=user.sex
        )
        try:
            self.db.add(new_user)
            await self.db.commit()
            await self.db.refresh(new_user)
            return new_user
        except IntegrityError:
            # Another transaction may have created the same username concurrently.
            await self.db.rollback()
            return None
        except Exception:
            # Ensure session rollback on error to avoid dirty transaction state
            await self.db.rollback()
            raise

    async def update_balance(self, user_id: int, amount: float):
        user = await self.get_by_id(user_id)
        if not user:
            return None
        user.balance += amount
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def get_budget(self, user_id: int, category: str):
        user = await self.get_by_id(user_id)
        if not user:
            return None
        budget_attr = CATEGORY_BUDGET_MAP.get(category)
        if not budget_attr:
            return 0.0
        return getattr(user, budget_attr, 0)
    
    async def get_monthly_budget(self, user_id: int):
        user = await self.get_by_id(user_id)
        if not user:
            return None
        monthly_budget = sum(getattr(user, budget_attr, 0) for budget_attr in CATEGORY_BUDGET_MAP.values()) 
        return monthly_budget

class SavingRepository(BaseRepository):
    async def create(self, user_id: int, target: sche_saving.CreateTarget):
        new_target = models.FinanceGoal(
            user_id=user_id,
            name=target.name,
            description=target.description,
            start_date=target.start_date,
            end_date=target.end_date,
            current_amount=target.current_amount,
            target_amount=target.target_amount,
        )
        self.db.add(new_target)
        await self.db.commit()
        await self.db.refresh(new_target)
        return new_target

    async def get_by_id(self, goal_id: int):
        target = await self.db.execute(select(models.FinanceGoal).filter(models.FinanceGoal.id == goal_id))
        return target.scalars().first()

    async def get_by_user_id_and_status(self, user_id: int, status: str):
        list_target = await self.db.execute(select(models.FinanceGoal).filter(
            models.FinanceGoal.user_id == user_id,
            models.FinanceGoal.status == status
        ))
        return list_target.scalars().all()

    async def get_all_by_user_id(self, user_id: int):
        list_target = await self.db.execute(select(models.FinanceGoal).filter(
            models.FinanceGoal.user_id == user_id
        ))
        return list_target.scalars().all()
    
    async def update_status(self, goal_id: int, status: str):
        goal = await self.get_by_id(goal_id)
        if not goal:
            return None
        goal.status = status
        await self.db.commit()
        await self.db.refresh(goal)
        return goal
    
    async def get_add_saving_amount(self, user_id: int):
        query = select(func.sum(models.FinanceGoal.current_amount)).filter(
            models.FinanceGoal.user_id == user_id
        )
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def get_total_target_save(self, user_id: int):
        query = select(func.sum(models.FinanceGoal.target_amount)).filter(
            models.FinanceGoal.user_id == user_id
        )
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def get_nearest_end_date(self, user_id: int):
        from datetime import date as date_type
        query = select(models.FinanceGoal.end_date).filter(
            models.FinanceGoal.user_id == user_id,
            models.FinanceGoal.end_date >= date_type.today(),
            models.FinanceGoal.status != "Completed"
        ).order_by(models.FinanceGoal.end_date).limit(1)
        result = await self.db.execute(query)
        end_date = result.scalar()
        if end_date:
            days_remaining = (end_date - date_type.today()).days
            return max(0, days_remaining)
        return 0

    async def update_current_amount(self, goal_id: int, amount: float):
        goal = await self.get_by_id(goal_id)
        if not goal:
            return None
        goal.current_amount += amount
        if goal.current_amount >= goal.target_amount:
            goal.status = "Completed"
        await self.db.commit()
        await self.db.refresh(goal)
        return goal

    async def check_and_update_failed_status(self, goal_id: int):
        goal = await self.get_by_id(goal_id)
        if not goal:
            return None
        from datetime import date
        today = date.today()
        if goal.end_date and today > goal.end_date and goal.current_amount < goal.target_amount and goal.status != "Completed":
            goal.status = "Failed"
            await self.db.commit()
            await self.db.refresh(goal)
        return goal

    async def delete(self, goal_id: int):
        goal = await self.get_by_id(goal_id)
        if not goal:
            return False
        await self.db.delete(goal)
        await self.db.commit()
        return True

class TransactionRepository(BaseRepository):
    async def create(self, user_id: int, data: sche_transaction.CreateTransaction, insufficient_balance):
        if insufficient_balance:
            description = "INSUFFICIENT_BALANCE"
        else:
            description = data.description
        new_transaction = models.Transaction(
            user_id=user_id,
            date=data.date,
            amount=data.amount,
            category=data.category,
            subscription_id=data.subscription_id,
            goal_id=data.goal_id,
            description=description,
        )
        self.db.add(new_transaction)
        await self.db.commit()
        await self.db.refresh(new_transaction)
        return new_transaction

    async def categorize(self, transaction_id: int, data: str):
        transaction = await self.get_by_id(transaction_id)
        transaction.category = data
        await self.db.commit()
        await self.db.refresh(transaction)
        return transaction

    async def view_uncategorized_transaction(self, user_id: int):
        list_transaction = await self.db.execute(select(models.Transaction).filter(
            models.Transaction.user_id == user_id,
            models.Transaction.category == "uncategorized"
        ))
        return list_transaction.scalars().all()

    async def get_by_id(self, transaction_id: int):
        transaction = await self.db.execute(select(models.Transaction).filter(
            models.Transaction.id == transaction_id
        ))
        return transaction.scalars().first()

    async def get_count_cate_transaction(self, user_id: int, loopback: int, category: str | None = None, type: str | None = "Day") -> int:
        if type == "Day":
            end_date = date.today()
            start_date = end_date - timedelta(days=loopback)
            query = select(func.count(models.Transaction.id)).filter(
                models.Transaction.user_id == user_id,
                func.date(models.Transaction.date) >= start_date,
                func.date(models.Transaction.date) <= end_date
            )
        else:
            now = datetime.now()
            _loopback_ago = now - timedelta(hours=loopback)
            query = select(func.count(models.Transaction.id)).filter(
                models.Transaction.user_id == user_id,
                models.Transaction.date >= _loopback_ago,
                models.Transaction.date <= now
            )

        if category is not None:
            query = query.filter(models.Transaction.category == category)
        else:
            query = query.filter(models.Transaction.category != "income")

        result = await self.db.execute(query)
        return result.scalar() or 0


    async def get_sum_cate_transaction(self, user_id: int, loopback: int, category: str | None = None, type: str | None = "Day") -> float:
        if type == "Day":
            end_date = date.today()
            start_date = end_date - timedelta(days=loopback)
            query = select(func.sum(models.Transaction.amount)).filter(
                models.Transaction.user_id == user_id,
                func.date(models.Transaction.date) >= start_date,
                func.date(models.Transaction.date) <= end_date
            )
        else:
            now = datetime.now()
            _loopback_ago = now - timedelta(hours=loopback)
            query = select(func.sum(models.Transaction.amount)).filter(  
                models.Transaction.user_id == user_id,
                models.Transaction.date >= _loopback_ago,
                models.Transaction.date <= now
            )

        if category is not None:
            query = query.filter(models.Transaction.category == category)
        else:
            query = query.filter(models.Transaction.category != "income")

        result = await self.db.execute(query)
        return result.scalar() or 0.0

    async def get_monthly_income(self, user_id: int, start_date: date, end_date: date) -> float:
        income_query = select(
            func.sum(models.Transaction.amount).label("total_income")
        ).filter(
            models.Transaction.user_id == user_id,
            models.Transaction.category == "income",
            func.date(models.Transaction.date) >= start_date,
            func.date(models.Transaction.date) <= end_date
        )

        result = await self.db.execute(income_query)
        return result.scalar() or 0.0

    # spending structure
    async def get_spending_structure(self, user_id: int, start_date: date, end_date: date):
        spending_query = select(
            models.Transaction.category,
            func.sum(models.Transaction.amount).label("total"),
        ).filter(
            models.Transaction.user_id == user_id,
            models.Transaction.description != "INSUFFICIENT_BALANCE",
            func.date(models.Transaction.date) >= start_date,
            func.date(models.Transaction.date) <= end_date
        ).group_by(models.Transaction.category)

        result = await self.db.execute(spending_query)
        spending_structure = {row.category: row.total for row in result.all()}
        return spending_structure

    async def get_all_spending(self, user_id: int, start_date: date, end_date: date):
        spending_obj = await self.db.execute(select(func.sum(models.Transaction.amount)).filter(
            models.Transaction.user_id == user_id,
            models.Transaction.description != "INSUFFICIENT_BALANCE",
            func.date(models.Transaction.date) >= start_date,
            func.date(models.Transaction.date) <= end_date,
            models.Transaction.category != "income"
        ))
        return spending_obj.scalar() or 0

    # spending behavior
    async def get_monthly_spending(self, user_id: int, start_date: date, end_date: date):
        spending_query = select(
            func.date(models.Transaction.date).label("day"),
            func.sum(models.Transaction.amount).label("total"),
        ).filter(
            models.Transaction.user_id == user_id,
            func.date(models.Transaction.date) >= start_date,
            func.date(models.Transaction.date) <= end_date,
            models.Transaction.category != "income",
            models.Transaction.description != "INSUFFICIENT_BALANCE",
        ).group_by(
            func.date(models.Transaction.date)
        )

        result = await self.db.execute(spending_query)
        spending_map = {row.day: row.total for  row in result.all()}
        return spending_map

    async def get_weekly_spending(self, user_id: int, start_date: date, end_date: date):
        week_label = func.date_trunc("week", models.Transaction.date).label("week_start")

        spending_query = (
            select(
                week_label,
                func.sum(models.Transaction.amount).label("total"),
            )
            .filter(
                models.Transaction.user_id == user_id,
                func.date(models.Transaction.date) >= start_date,
                func.date(models.Transaction.date) <= end_date,
                models.Transaction.category != "income",
                models.Transaction.description != "INSUFFICIENT_BALANCE",
            )
            .group_by(week_label)
            .order_by("week_start")
        )

        result = await self.db.execute(spending_query)
        spending_map = {row.week_start.date(): row.total for row in result.all()}
        return spending_map

    async def get_non_essential_stats(self, user_id: int, start_date: date, end_date: date,
                                      non_essential_categories: list[str]):
        """
        Trả về (non_essential_count, total_count, non_essential_amount, total_amount)
        trong khoảng thời gian cho PRS s_impulse.
        """
        base_filter = [
            models.Transaction.user_id == user_id,
            func.date(models.Transaction.date) >= start_date,
            func.date(models.Transaction.date) <= end_date,
            models.Transaction.category != "income",
            models.Transaction.description != "INSUFFICIENT_BALANCE",
        ]

        total_query = select(
            func.count(models.Transaction.id).label("cnt"),
            func.sum(models.Transaction.amount).label("amt"),
        ).filter(*base_filter)
        total_result = await self.db.execute(total_query)
        total_row = total_result.first()
        total_count = total_row.cnt or 0
        total_amount = float(total_row.amt or 0.0)

        ne_query = select(
            func.count(models.Transaction.id).label("cnt"),
            func.sum(models.Transaction.amount).label("amt"),
        ).filter(
            *base_filter,
            models.Transaction.category.in_(non_essential_categories)
        )
        ne_result = await self.db.execute(ne_query)
        ne_row = ne_result.first()
        non_essential_count = ne_row.cnt or 0
        non_essential_amount = float(ne_row.amt or 0.0)

        return non_essential_count, total_count, non_essential_amount, total_amount

    async def get_late_night_non_essential_count(self, user_id: int, start_date: date, end_date: date,
                                                  non_essential_categories: list[str]) -> tuple[int, int]:
        """
        Trả về (late_night_non_essential_count, total_count).
        Late night: 23:00 – 05:00.
        """
        base_filter = [
            models.Transaction.user_id == user_id,
            func.date(models.Transaction.date) >= start_date,
            func.date(models.Transaction.date) <= end_date,
            models.Transaction.category != "income",
            models.Transaction.description != "INSUFFICIENT_BALANCE",
        ]

        total_query = select(func.count(models.Transaction.id)).filter(*base_filter)
        total_result = await self.db.execute(total_query)
        total_count = total_result.scalar() or 0

        hour_col = func.extract("hour", models.Transaction.date)
        late_night_query = select(func.count(models.Transaction.id)).filter(
            *base_filter,
            models.Transaction.category.in_(non_essential_categories),
            # 23:00 – 23:59 hoặc 00:00 – 04:59
            (hour_col >= 23) | (hour_col < 5)
        )
        late_result = await self.db.execute(late_night_query)
        late_count = late_result.scalar() or 0

        return late_count, total_count

    async def get_monthly_income_list(self, user_id: int, months: int) -> list[float]:
        """
        Trả về danh sách tổng thu nhập theo từng tháng trong `months` tháng gần nhất.
        """
        today = date.today()
        results = []
        for i in range(months - 1, -1, -1):
            # Tính start/end của tháng cách hiện tại i tháng
            month = today.month - i
            year = today.year
            while month <= 0:
                month += 12
                year -= 1
            start = date(year, month, 1)
            if month == 12:
                end = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end = date(year, month + 1, 1) - timedelta(days=1)
            income = await self.get_monthly_income(user_id, start, end)
            results.append(income)
        return results

    async def get_monthly_expense_list(self, user_id: int, months: int) -> list[float]:
        """
        Trả về danh sách tổng chi tiêu theo từng tháng trong `months` tháng gần nhất.
        """
        today = date.today()
        results = []
        for i in range(months - 1, -1, -1):
            month = today.month - i
            year = today.year
            while month <= 0:
                month += 12
                year -= 1
            start = date(year, month, 1)
            if month == 12:
                end = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end = date(year, month + 1, 1) - timedelta(days=1)
            expense = await self.get_all_spending(user_id, start, end)
            results.append(float(expense))
        return results

    async def get_monthly_goal_contributions(self, user_id: int, months: int) -> list[float]:
        """
        Trả về tổng tiền nạp vào goal theo từng tháng (qua transaction có goal_id).
        """
        today = date.today()
        results = []
        for i in range(months - 1, -1, -1):
            month = today.month - i
            year = today.year
            while month <= 0:
                month += 12
                year -= 1
            start = date(year, month, 1)
            if month == 12:
                end = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end = date(year, month + 1, 1) - timedelta(days=1)

            query = select(func.sum(models.Transaction.amount)).filter(
                models.Transaction.user_id == user_id,
                models.Transaction.goal_id.isnot(None),
                func.date(models.Transaction.date) >= start,
                func.date(models.Transaction.date) <= end,
            )
            result = await self.db.execute(query)
            results.append(float(result.scalar() or 0.0))
        return results

    async def get_category_overshoot_list(self, user_id: int, start_date: date, end_date: date,
                                           budget_map: dict[str, float]) -> list[float]:
        """
        Tính overshoot ratio cho từng category có budget.
        Overshoot = max(0, (spent - budget) / budget).
        Trả về list các giá trị overshoot (kể cả 0.0 nếu không vượt).
        """
        spending_by_category = await self.get_spending_structure(user_id, start_date, end_date)
        overshoots = []
        for cat, budget in budget_map.items():
            if budget <= 0:
                continue
            spent = spending_by_category.get(cat, 0.0)
            overshoots.append(max(0.0, (spent - budget) / budget))
        return overshoots

    async def get_essential_spending(self, user_id: int, start_date: date, end_date: date,
                                      essential_categories: list[str]) -> float:
        """
        Tổng chi tiêu cho các category thiết yếu.
        """
        query = select(func.sum(models.Transaction.amount)).filter(
            models.Transaction.user_id == user_id,
            func.date(models.Transaction.date) >= start_date,
            func.date(models.Transaction.date) <= end_date,
            models.Transaction.category.in_(essential_categories),
            models.Transaction.description != "INSUFFICIENT_BALANCE",
        )
        result = await self.db.execute(query)
        return float(result.scalar() or 0.0)

    async def get_transactions_in_range(self, user_id: int, start_date: date, end_date: date) -> list:
        """
        Lấy toàn bộ transaction trong khoảng thời gian (dùng cho r_recovery).
        """
        query = select(models.Transaction).filter(
            models.Transaction.user_id == user_id,
            func.date(models.Transaction.date) >= start_date,
            func.date(models.Transaction.date) <= end_date,
        ).order_by(models.Transaction.date)
        result = await self.db.execute(query)
        return result.scalars().all()
    

class SubscriptionRepository(BaseRepository):
    async def create(self, user_id: int, data: sche_subscription.CreateSubscription):
        subscription_query = await self.get_subscription_by_user(user_id, data.service_name)
        if subscription_query:
            subscription_query.is_active = True
            await self.db.commit()
            await self.db.refresh(subscription_query)
            return subscription_query

        new_subscription = models.Subscription(
            user_id=user_id,
            service_name=data.service_name.lower(),
            amount=data.amount,
            billing_cycle=data.billing_cycle,
            next_billing_date=data.next_billing_date,
            is_active=data.is_active,
        )

        self.db.add(new_subscription)
        await self.db.commit()
        await self.db.refresh(new_subscription)
        return new_subscription

    async def update_next_billing_date(self, subscription_id: int, new_next_billing_date: date):
        current_subscription = await self.get_by_id(subscription_id)
        if current_subscription:
            current_subscription.next_billing_date = new_next_billing_date
            await self.db.commit()
            await self.db.refresh(current_subscription)
        return current_subscription

    async def my_subscription(self, user_id: int):
        list_subscription = await self.db.execute(select(models.Subscription).filter(
            models.Subscription.user_id == user_id,
            models.Subscription.is_active == True
        ))
        return list_subscription.scalars().all()

    async def get_by_id(self, subscription_id: int):
        subscription = await self.db.execute(select(models.Subscription).filter(
            models.Subscription.id == subscription_id
        ))
        return subscription.scalars().first()
 

    async def get_subscription_by_user(self, user_id: int, service_name: str):
        subscription = await self.db.execute(select(models.Subscription).filter(
            models.Subscription.user_id == user_id,
            models.Subscription.service_name == service_name.lower()
        ))
        return subscription.scalars().first()
    
    async def deactivate(self, subscription_id: int):
        subscription = await self.get_by_id(subscription_id)
        if not subscription:
            return False
        subscription.is_active = False
        subscription.switch_date = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(subscription)
        return subscription
    
    async def delete(self, subscription_id: int):
        subscription = await self.get_by_id(subscription_id)
        print(subscription_id)
        if not subscription:
            return False
        await self.db.delete(subscription)
        await self.db.commit()
        return True
    
    async def get_cancelled_count_last_14d(self, user_id: int) -> int:
        """
        Dem so subscription bi cancel trong 14 ngay gan nhat.
        Dua vao is_active=False va cancelled_at trong khoang thoi gian.
        """
        cutoff = datetime.utcnow() - timedelta(days=14)
        query = select(func.count(models.Subscription.id)).filter(
            models.Subscription.user_id == user_id,
            models.Subscription.is_active == False,
            models.Subscription.switch_date >= cutoff,
        )
        result = await self.db.execute(query)
        return result.scalar() or 0
 
    async def get_total_count(self, user_id: int) -> int:
        """
        Dem tong so subscription (ca active lan cancelled) cua user.
        """
        query = select(func.count(models.Subscription.id)).filter(
            models.Subscription.user_id == user_id,
        )
        result = await self.db.execute(query)
        return result.scalar() or 0















