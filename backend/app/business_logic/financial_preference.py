from repo.repositories import TransactionRepository, UserRepository, SavingRepository, SubscriptionRepository
from schemas import transaction as sche_transaction, irs as sche_irs, prs as sche_prs, resilience as sche_resilience
import numpy as np
from datetime import date, timedelta, datetime
import math

NON_ESSENTIAL_CATEGORIES = ["shopping", "entertainment", "other"]
ESSENTIAL_CATEGORIES     = ["food and drink", "moving", "investment"]
CATEGORY_BUDGET_MAP_KEYS = ["food and drink", "shopping", "investment", "moving", "entertainment", "other"]

LAMBDA_DECAY = 0.8
EPS = 1e-8

def sigmoid(x: float) -> float:
    try:
        return 1.0 / (1.0 + math.exp(-max(-20, min(20, x))))
    except:
        return 0.5 if x == 0 else (1.0 if x > 0 else 0.0)

def mean(x: list, k: int | None = None) -> float:
    if not x:
        return 0.0

    if k == 0:
        return sum([max(i, 0) for i in x]) / len(x)
    elif k == 1:
        return sum([min(i, 1) for i in x]) / len(x)
    return float(np.mean(x))

def std(x: list) -> float:
    if not x:
        return 0.0
    return np.std(x)

class ImmediateRegretScore:
    def __init__(self,
                 budget_breach: sche_irs.BudgetBreach,
                 income_proportion_shock: sche_irs.IncomeProportionShock,
                 temporal_vulnerability: sche_irs.TemporalVulnerability,
                 goal_conflict_severity: sche_irs.GoalConflictSeverity,
                 category_frequency_anomaly: sche_irs.CategoryFrequencyAnomaly,
                 category_risk_profile: sche_irs.CategoryRiskProfile,
                 day_of_month_timing: sche_irs.DayOfMonthTiming,
                 spending_velocity: sche_irs.SpendingVelocity
                 ):
        self.budget_breach = budget_breach
        self.income_proportion_shock = income_proportion_shock
        self.temporal_vulnerability = temporal_vulnerability
        self.goal_conflict_severity = goal_conflict_severity
        self.category_frequency_anomaly = category_frequency_anomaly
        self.category_risk_profile = category_risk_profile
        self.day_of_month_timing = day_of_month_timing
        self.spending_velocity = spending_velocity

    def calculate_s_budget(self):
        category_spend = self.budget_breach.category_spent
        category_budget = self.budget_breach.category_budget
        txn_amount = self.budget_breach.txn_amount

        remaining = max(EPS, category_budget - category_spend)
        s_budget = min(1.0, max(0.0, txn_amount / remaining))
        return s_budget

    def calculate_s_income(self):
        txn_amount = self.income_proportion_shock.txn_amount
        monthly_income = self.income_proportion_shock.monthly_income

        s_income = min(1.0, (txn_amount / (monthly_income + EPS)) ** 0.7)
        return s_income

    def calculate_s_time(self):
        txn_time = self.temporal_vulnerability.txn_datetime
        h = txn_time.hour
        if 6 <= h < 21:
            return 0.0
        elif 21 <= h < 23:
            return 0.3
        elif h == 23 or h == 0:
            return 0.7
        elif 1 <= h < 5:
            return 1.0
        else:  # 5 <= h < 6
            return 0.5

    def calculate_s_goal(self):
        goals_data = self.goal_conflict_severity.goals_data
        txn_amount = self.goal_conflict_severity.txn_amount
        if not goals_data:
            return 0.0

        s_goal = 0.0
        for goal in goals_data:
            target_amount  = goal.get("target_amount", 0)
            current_amount = goal.get("current_amount", 0)
            end_date       = goal.get("end_date")

            remaining_needed = target_amount - current_amount
            if remaining_needed <= 0:
                # Goal đã hoàn thành, bỏ qua
                continue

            if end_date is None:
                # Không có deadline → dùng hệ số urgency mặc định thấp
                urgency = 30 / 365
            else:
                today = date.today()
                raw_days_left = (end_date - today).days
                if raw_days_left <= 0:
                    # Goal đã quá hạn nhưng chưa completed → urgency cao nhất
                    days_left = 1
                else:
                    days_left = raw_days_left
                urgency = 30 / days_left

            impact = min(1.0, (txn_amount / (remaining_needed + EPS)) * urgency)
            s_goal = max(s_goal, impact)

        return s_goal

    def calculate_s_frequency(self):
        recent_count = self.category_frequency_anomaly.recent_count
        # baseline_weekly_count đã là trung bình tuần (count 90 ngày / 12.86), không cần chia lại
        baseline_weekly_count = self.category_frequency_anomaly.baseline_weekly_count

        s_freq = min(1.0, max(0.0, (recent_count - baseline_weekly_count) / max(baseline_weekly_count + EPS, 1.0)))
        return s_freq

    def calculate_s_category_risk(self):
        return self.category_risk_profile.risk_score

    def calculate_s_day_of_month(self):
        monthly_budget = self.day_of_month_timing.monthly_budget
        total_spent = self.day_of_month_timing.total_spent
 
        # Tính budget_remaining SAU khi cộng txn hiện tại để đo đúng áp lực gây ra bởi giao dịch này
        budget_remaining_ratio = max(0.0, (monthly_budget - total_spent) / (monthly_budget + EPS))
 
        today = date.today()
        if today.month == 12:
            first_next_month = date(today.year + 1, 1, 1)
        else:
            first_next_month = date(today.year, today.month + 1, 1)
        days_left_in_month = (first_next_month - today).days
 
        # Clamp về [0, 1]: tháng 31 ngày vào ngày 1 → days_left=30 → ratio=1.0 đúng
        # nhưng tháng 31 ngày vào ngày 31 → days_left=1, không bao giờ > 1 nếu chia cho days_in_month
        days_in_month = (first_next_month - date(today.year, today.month, 1)).days
        month_remaining_ratio = min(1.0, days_left_in_month / days_in_month)
 
        s_dom = max(0.0, month_remaining_ratio - budget_remaining_ratio)
        return s_dom

    def calculate_s_spending_velocity(self):
        txns_last_2h = self.spending_velocity.txns_last_2h
        amount_last_2h = self.spending_velocity.amount_last_2h
        daily_budget = self.spending_velocity.daily_budget
        # daily_budget is average daily budget for the month daily_budget = monthly_budget / 30

        s_vel = min(1, (txns_last_2h / 5) * 0.5 + (amount_last_2h / (daily_budget + EPS)) * 0.5)
        return s_vel
    
    def result(self):
        irs = sche_irs.ImmediateRegretScore(
            s_budget=self.calculate_s_budget(),
            s_income=self.calculate_s_income(),
            s_time=self.calculate_s_time(),
            s_goal=self.calculate_s_goal(),
            s_freq=self.calculate_s_frequency(),
            s_cat=self.calculate_s_category_risk(),
            s_dom=self.calculate_s_day_of_month(),
            s_vel=self.calculate_s_spending_velocity()
        )

        return irs.model_dump()

# rollback_days = 14
class PeriodicRegretScore:
    def __init__(self, 
                 impulse_spending: sche_prs.ImpulseSpending,
                 budget_over_shoot: sche_prs.BudgetOvershoot,
                 goal_disruption: sche_prs.GoalDisruption,
                 subscription_churn_signal: sche_prs.SubscriptionChurnSignal,
                 late_night_spending: sche_prs.LateNightSpending,
                 expense_to_income_pressure: sche_prs.ExpenseToIncomePressure,
                 ):
        self.impulse_spending = impulse_spending
        self.budget_over_shoot = budget_over_shoot
        self.goal_disruption = goal_disruption
        self.subscription_churn_signal = subscription_churn_signal
        self.late_night_spending = late_night_spending
        self.expense_to_income_pressure = expense_to_income_pressure
 
    def calculate_s_impulse(self):
        non_essential_count  = self.impulse_spending.non_essential_count
        total_count          = self.impulse_spending.total_count
        non_essential_amount = self.impulse_spending.non_essential_amount
        total_amount         = self.impulse_spending.total_amount
 
        freq_ratio   = non_essential_count  / (total_count  + EPS)
        amount_ratio = non_essential_amount / (total_amount + EPS)
 
        s_impulse = min(1.0, 0.5 * freq_ratio + 0.5 * amount_ratio)
        return s_impulse
 
    def calculate_s_budget(self):
        category_overshoots = self.budget_over_shoot.category_overshoots
        if not category_overshoots:
            return 0.0
 
        # Fix: sigmoid(2*x) cũ cho floor=0.5 khi x=0 (không vượt budget)
        # Dùng 2*sigmoid(3*x)-1 clamp [0,1] → = 0 khi không vượt budget
        mean_overshoot = mean(category_overshoots, 0)
        s_budget = max(0.0, min(1.0, 2 * sigmoid(3 * mean_overshoot) - 1))
        return s_budget
    
    def calculate_s_goal(self):
        goals_data = self.goal_disruption.goals_data
        if not goals_data: 
            return 0.0
 
        disruption_scores = []
        for goal in goals_data:
            remaining = goal["target_amount"] - goal["current_amount"]
            if remaining <= 0:
                continue
            days_left = max((goal["end_date"] - date.today()).days, 1)
            non_goal_spending = goal["spending_toward_goal"]
 
            ratio = non_goal_spending / (remaining + EPS)
            daily_needed_now = remaining / days_left
            daily_needed_counterfactual = max(remaining - non_goal_spending, 0) / days_left
            velocity_change = daily_needed_now / (daily_needed_counterfactual + EPS)
 
            # Fix: sigmoid(velocity_change - 1) khi spend=0 → vel=1 → sigmoid(0)=0.5
            # → vel_part = 0.4*0.5 = 0.2 dù không có gì ảnh hưởng (floor artifact)
            # Fix: dùng 2*(sigmoid(vel-1)-0.5) clamp [0,1] → = 0 khi vel=1 (spend=0)
            vel_part = max(0.0, 2 * (sigmoid(velocity_change - 1) - 0.5))
            disruption_scores.append(0.6 * min(ratio, 1) + 0.4 * vel_part)
 
        s_goal = mean(disruption_scores, None)
 
        return s_goal
 
    def calculate_s_subscription(self):
        cancelled_subscriptions_14d = self.subscription_churn_signal.cancelled_subscriptions_14d
        total_subscriptions = self.subscription_churn_signal.total_subscriptions
        if not cancelled_subscriptions_14d:
            return 0.0
 
        s_sub = min(cancelled_subscriptions_14d / (total_subscriptions + EPS), 1.0)
        return s_sub
 
        # remember to change the subscript create (same name -> switch "is_active"), delete (switch "is_active") logic
 
    def calculate_s_night(self):
        late_night_non_essential = self.late_night_spending.late_night_non_essential_count
        total_count = self.late_night_spending.total_transaction_count
 
        # NOTE: repo query phải dùng (hour >= 23 OR hour <= 5) để nhất quán với
        # IRS TemporalVulnerability (5:00-6:00 vẫn có s_time=0.5).
        # repositories.py hiện dùng hour < 5 (sai) → cần sửa thành hour <= 5
        s_night = late_night_non_essential / (total_count + EPS)
        return s_night
 
    def calculate_s_pressure(self):
        total_income = self.expense_to_income_pressure.total_income
        total_expenses = self.expense_to_income_pressure.total_expenses
        if total_income <= 0:
            return 1.0
 
        s_pressure = sigmoid(3 * (total_expenses / (total_income + EPS) - 0.7))
        return s_pressure
    
    def result(self):
        prs = sche_prs.PeriodicRegretScore(
            s_impulse=self.calculate_s_impulse(),
            s_budget=self.calculate_s_budget(),
            s_goal=self.calculate_s_goal(),
            s_sub=self.calculate_s_subscription(),
            s_night=self.calculate_s_night(),
            s_pressure=self.calculate_s_pressure()
        )
 
        return prs.model_dump()
    
class ResilienceLevel:
    def __init__(self,
                 balance_recovery: sche_resilience.BalanceRecoverySpeed,
                 goal_funding: sche_resilience.GoalFundingConsistency,
                 spending_structure: sche_resilience.SpendingStructure,
                 spending_entropy: sche_resilience.SpendingEntropy,
                 budget_adherence: sche_resilience.BudgetAdherence,
                 savings_rate: sche_resilience.SavingsRateConsistency,
                 income_stability: sche_resilience.IncomeVolatilityAbsorption
                 ):
        self.balance_recovery = balance_recovery
        self.goal_funding = goal_funding
        self.spending_structure = spending_structure
        self.spending_entropy = spending_entropy
        self.budget_adherence = budget_adherence
        self.savings_rate = savings_rate
        self.income_stability = income_stability

    def calculate_r_recovery(self, shock_pct=0.15):
        """
        Mô phỏng khả năng phục hồi số dư sau các khoảng chi tiêu lớn.
        Với mỗi ngày mà cumulative balance dưới threshold (income * shock_pct),
        tính độ trễ phục hồi rồi trung bình exp(-0.05 * d).
        """
        income    = self.balance_recovery.income
        threshold = income * shock_pct
        txns      = self.balance_recovery.txns  # list of dict: {"amount": float, "date": date}

        if not txns:
            return 0.5

        # Sắp xếp theo ngày
        sorted_txns = sorted(txns, key=lambda t: t["date"])

        # Tính running balance và phát hiện các đợt dip (dưới threshold)
        running = 0.0
        dip_recovery_days: list[int] = []
        dip_start: date | None = None

        for txn in sorted_txns:
            running += txn["amount"]  # income dương, expense âm
            txn_date = txn["date"] if isinstance(txn["date"], date) else txn["date"].date()

            if running < threshold:
                if dip_start is None:
                    dip_start = txn_date
            else:
                if dip_start is not None:
                    recovery_days = (txn_date - dip_start).days
                    dip_recovery_days.append(recovery_days)
                    dip_start = None

        if not dip_recovery_days:
            # Không phát hiện dip nào trong window 4 tháng.
            # Có 2 khả năng: (a) user thực sự ổn định, hoặc (b) không đủ dữ liệu / balance luôn âm.
            # Kiểm tra: nếu cuối window vẫn đang trong dip (chưa recover) → penalize
            if dip_start is not None:
                # Đang trong dip và chưa recover → score thấp
                return 0.30
            # Thực sự không có dip → score tốt nhưng không phải 1.0
            # (1.0 chỉ có ý nghĩa nếu có ít nhất 1 dip và recover nhanh)
            return 0.85  # không có dip = tốt, nhưng không "perfect" vì thiếu evidence

        r_recovery = float(np.mean([np.exp(-0.05 * d) for d in dip_recovery_days]))
        return r_recovery

    def calculate_r_goal(self):
        monthly_goal_contributions = self.goal_funding.monthly_goal_contributions

        if not monthly_goal_contributions:
            return 0.0

        total_months = len(monthly_goal_contributions)
        c_std  = std(monthly_goal_contributions)
        c_mean = mean(monthly_goal_contributions)
        cv = c_std / (c_mean + EPS)
        participation = sum(1 for c in monthly_goal_contributions if c > 0) / total_months

        r_goal = 0.6 * float(np.exp(-cv)) + 0.4 * participation
        return r_goal
    
    def calculate_r_structure(self):
        essential_spending = self.spending_structure.essential_spending
        total_spending = self.spending_structure.total_spending

        r = essential_spending / (total_spending + EPS)
        optimal = 0.6

        r_structure = np.exp(-(r - optimal) ** 2 / 0.08)
        return r_structure
    
    def calculate_r_entropy(self):
        """
        R_entropy V3: Shannon entropy / ln(K), clamp [0,1].

        Bug cũ: khi k=1, max_ent = ln(1+EPS) ≈ 0 → division by ~0 → r_entropy ≈ -1.0 (ÂM).
        Giá trị âm × beta4=0.70 làm GIẢM weighted_sum → kéo resilience xuống không đúng pattern.
        (Ngược lại, nếu weight âm thì sẽ kéo lên — đây là bug semantic nguy hiểm.)

        Fix:
          k=0 → 0.5 (unknown)
          k=1 → 0.25 (single category = concentrated, nhưng có thể là hoàn cảnh)
          k≥2 → clamp max(0, entropy/max_ent)
        """
        category_spending_prop = self.spending_entropy.category_spending_amounts
        k = len(category_spending_prop)

        if k == 0:
            return 0.5
        if k == 1:
            return 0.25  # partial credit — single category, không phạt quá nặng

        total = sum(category_spending_prop.values())
        if total <= 0:
            return 0.5

        props   = [v / total for v in category_spending_prop.values() if v > 0]
        k_eff   = len(props)  # chỉ đếm category thực sự có chi tiêu
        if k_eff == 1:
            return 0.25

        entropy = -sum(p * np.log(p + EPS) for p in props)
        max_ent = np.log(k_eff)   # dùng k_eff thay vì k+EPS để tránh log(1+EPS)≈0

        r_entropy = max(0.0, min(1.0, entropy / (max_ent + EPS)))
        return r_entropy
    
    def calculate_r_adherence(self):
        """
        R_adherence V3: 0.0 khi không set budget (thay vì 0.5).

        Bug cũ: return 0.5 khi overshoots = [] → user không set budget nhận điểm trung bình.
        Điều này inflate resilience vì 1.40 * 0.5 = 0.7 vào weighted_sum mà không làm gì.

        Fix: không set budget = không có thông tin → 0.0 (không thưởng không phạt nghiêm)
        Khuyến khích user set budget để có điểm r_adherence thực sự.
        """
        category_overshoots = self.budget_adherence.category_overshoots
        if not category_overshoots:
            return 0.0  # không set budget → không có adherence data

        r_adherence = mean([float(np.exp(-max(0, o))) for o in category_overshoots])
        return r_adherence
    
    def calculate_r_saving(self):
        """
        R_saving V3: exclude tháng income=0 khỏi avg_rate (freelancer fairness).

        Bug cũ: tháng income=0 → rate = (0-E)/EPS → clamp về -1.0.
        Freelancer không có dự án 1 tháng bị penalize mạnh dù tháng khác tiết kiệm tốt.

        Fix: tính avg_rate chỉ trên tháng có income > 0.
        std_rate vẫn tính trên tất cả để capture volatility thực sự.
        """
        monthly_expense = np.array(self.savings_rate.monthly_expenses)
        monthly_income  = np.array(self.savings_rate.monthly_income)

        all_rates = np.maximum(-1.0, (monthly_income - monthly_expense) / (monthly_income + EPS))
        # std tính trên tất cả tháng (capture volatility)
        std_rate = np.std(all_rates)

        # avg chỉ tính trên tháng có income > 0
        active_mask = monthly_income > 0
        if np.any(active_mask):
            active_rates = np.maximum(-1.0, (
                (monthly_income[active_mask] - monthly_expense[active_mask])
                / (monthly_income[active_mask] + EPS)
            ))
            avg_rate = float(np.mean(active_rates))
        else:
            avg_rate = -1.0  # không có income nào → rất xấu

        r_saving = 0.5 * sigmoid(5 * avg_rate) + 0.5 * np.exp(-2 * std_rate)
        return r_saving

    def calculate_r_income(self):
        monthly_income = self.income_stability.monthly_income
        if sum(monthly_income) == 0:
            return 0.3

        avg_income = np.mean(monthly_income)
        std_income = np.std(monthly_income)
        cv = std_income / (avg_income + EPS)

        r_income = np.exp(-1.5 * cv)
        return r_income

    def result(self):
        resilience = sche_resilience.ResilienceScore(
            r_recovery=self.calculate_r_recovery(),
            r_goal=self.calculate_r_goal(),
            r_structure=self.calculate_r_structure(),
            r_entropy=self.calculate_r_entropy(),
            r_adherence=self.calculate_r_adherence(),
            r_saving=self.calculate_r_saving(),
            r_income=self.calculate_r_income()
        )

        return resilience.model_dump()

class FinancialPreferenceAnalyzer:
    def __init__(self,
                 user_repo: UserRepository,
                 transaction_repo: TransactionRepository,
                 subscription_repo: SubscriptionRepository,
                 saving_repo: SavingRepository):
        self.user_repo = user_repo
        self.transaction_repo = transaction_repo
        self.subscription_repo = subscription_repo
        self.saving_repo = saving_repo

    async def to_irs(self, user_id: int, transaction: sche_transaction.CreateTransaction) -> ImmediateRegretScore:
        category = transaction.category
        description = transaction.description
        txn_amount = transaction.amount
        txn_datetime = transaction.date

        category_budget = await self.user_repo.get_budget(user_id, category)
        # Tính spend từ đầu tháng của transaction đến hôm nay (không dùng loopback_in_month vì
        # get_sum_cate_transaction(loopback=N) tính start = today - N ngày → cross sang tháng trước)
        begin_this_month_for_budget = date(txn_datetime.year, txn_datetime.month, 1)
        days_since_month_start = (date.today() - begin_this_month_for_budget).days + 1
        category_spend = await self.transaction_repo.get_sum_cate_transaction(
            user_id, loopback=days_since_month_start, category=category
        )

        # Fallback s_budget: nếu category không có budget riêng, dùng monthly_budget
        monthly_budget_for_fallback = await self.user_repo.get_monthly_budget(user_id) or 0.0
        effective_category_budget = float(category_budget or 0.0)
        if effective_category_budget <= 0:
            # Fallback: dùng total monthly budget và total spending tháng này
            begin_this_month_for_budget2 = date(txn_datetime.year, txn_datetime.month, 1)
            total_spent_this_month = await self.transaction_repo.get_all_spending(
                user_id, begin_this_month_for_budget2, date.today()
            )
            effective_category_budget = float(monthly_budget_for_fallback)
            category_spend = float(total_spent_this_month)

        # s_budget
        budget_breach = sche_irs.BudgetBreach(
            category_budget=effective_category_budget,
            category_spent=float(category_spend),
            txn_amount=txn_amount,
        )

        if txn_datetime.month == 1:
            begin_last_month = date(txn_datetime.year - 1, 12, 1)
        else:
            begin_last_month = date(txn_datetime.year, txn_datetime.month - 1, 1)
        end_last_month = date(txn_datetime.year, txn_datetime.month, 1) - timedelta(days=1)
        monthly_income = await self.transaction_repo.get_monthly_income(user_id, begin_last_month, end_last_month)
        # Fallback: nếu tháng trước chưa có income (đầu tháng mới), dùng trung bình 3 tháng gần nhất
        if monthly_income == 0:
            income_list = await self.transaction_repo.get_monthly_income_list(user_id, months=3)
            non_zero = [v for v in income_list if v > 0]
            monthly_income = float(np.mean(non_zero)) if non_zero else 0.0

        # s_income
        income_shock = sche_irs.IncomeProportionShock(
            txn_amount=txn_amount,
            monthly_income=monthly_income  
        )

        # s_temporal
        temporal_vulnerability = sche_irs.TemporalVulnerability(
            txn_datetime=txn_datetime
        )

        # s_saving
        current_saving = await self.saving_repo.get_by_user_id_and_status(user_id, "Processing")
        goals_data = [
            {
                "target_amount": float(g.target_amount),
                "current_amount": float(g.current_amount),
                "end_date": g.end_date if isinstance(g.end_date, date) else date.fromisoformat(str(g.end_date)),
            }
            for g in current_saving
        ]
        goal_conflict_severity = sche_irs.GoalConflictSeverity(
            goals_data=goals_data, 
            txn_amount=txn_amount
        )

        # s_frequency
        cate_count_7d = await self.transaction_repo.get_count_cate_transaction(user_id, loopback=7, category=category)
        cate_count_90d = await self.transaction_repo.get_count_cate_transaction(user_id, loopback=90, category=category)
        baseline_weekly = cate_count_90d / (90 / 7)  # convert 90-day count -> weekly average
        category_frequency_anomaly = sche_irs.CategoryFrequencyAnomaly(
            recent_count=cate_count_7d,
            baseline_weekly_count=baseline_weekly
        )

        # s_risk
        category_risk_profile = sche_irs.CategoryRiskProfile(
            category=description
        )

        # s_dom
        monthly_budget = await self.user_repo.get_monthly_budget(user_id)
        begin_this_month = date(txn_datetime.year, txn_datetime.month, 1)
        total_spent = await self.transaction_repo.get_all_spending(user_id, begin_this_month, date.today())
        day_of_month_timing = sche_irs.DayOfMonthTiming(
            monthly_budget=monthly_budget,
            total_spent=total_spent,
        )

        # s_velocity
        txns_last_2h = await self.transaction_repo.get_count_cate_transaction(user_id, loopback=2, type="Hour")
        amount_last_2h = await self.transaction_repo.get_sum_cate_transaction(user_id, loopback=2, type="Hour")
        recent_activity = sche_irs.SpendingVelocity(
            txns_last_2h=txns_last_2h,
            amount_last_2h=amount_last_2h,
            daily_budget=monthly_budget / (30 + EPS)
        )

        irs = ImmediateRegretScore(
            budget_breach = budget_breach,
            income_proportion_shock = income_shock,
            temporal_vulnerability = temporal_vulnerability,
            goal_conflict_severity = goal_conflict_severity,
            category_frequency_anomaly = category_frequency_anomaly,
            category_risk_profile = category_risk_profile,
            day_of_month_timing = day_of_month_timing,
            spending_velocity = recent_activity
        )

        return irs.result()

    async def to_prs(self, user_id: int, lookback_days: int = 14) -> dict:
        today     = date.today()
        start     = today - timedelta(days=lookback_days)
 
        # s_impulse
        non_essential_count, total_count, non_essential_amount, total_amount = (
            await self.transaction_repo.get_non_essential_stats(
                user_id, start, today, NON_ESSENTIAL_CATEGORIES
            )
        )
        impulse_spending = sche_prs.ImpulseSpending(
            non_essential_count=non_essential_count,
            total_count=total_count,
            non_essential_amount=non_essential_amount,
            total_amount=total_amount,
        )
 
        # s_budget — overshoot từng category so với budget tháng này
        begin_this_month = date(today.year, today.month, 1)
        user = await self.user_repo.get_by_id(user_id)
        budget_map = {
            "food and drink": float(user.fad_budget or 0),
            "shopping":       float(user.shopping_budget or 0),
            "investment":     float(user.investment_budget or 0),
            "moving":         float(user.moving_budget or 0),
            "entertainment":  float(user.entertainment_budget or 0),
            "other":          float(user.other_budget or 0),
        }
        category_overshoots = await self.transaction_repo.get_category_overshoot_list(
            user_id, begin_this_month, today, budget_map
        )
        budget_overshoot = sche_prs.BudgetOvershoot(
            category_overshoots=category_overshoots
        )
 
        # s_goal — mức độ chi tiêu ngoài goal ảnh hưởng đến khả năng hoàn thành goal
        current_goals = await self.saving_repo.get_by_user_id_and_status(user_id, "Processing")
        total_expenses_in_period = await self.transaction_repo.get_all_spending(user_id, start, today)
        total_goal_contributions = await self.transaction_repo.get_monthly_goal_contributions(user_id, 1)
        # Chi tiêu không phải cho goal = tổng chi tiêu - tiền nạp vào goal
        non_goal_spending = float(total_expenses_in_period) - float(total_goal_contributions[0] if total_goal_contributions else 0)
        non_goal_spending = max(0.0, non_goal_spending)
        goals_data = []
        for g in current_goals:
            goals_data.append({
                "target_amount":        float(g.target_amount),
                "current_amount":       float(g.current_amount),
                "end_date":             g.end_date,
                "spending_toward_goal": non_goal_spending,
            })
        goal_disruption = sche_prs.GoalDisruption(goals_data=goals_data)
 
        # s_sub
        cancelled_14d = await self.subscription_repo.get_cancelled_count_last_14d(user_id)
        total_subs    = await self.subscription_repo.get_total_count(user_id)
        subscription_churn = sche_prs.SubscriptionChurnSignal(
            cancelled_subscriptions_14d=cancelled_14d,
            total_subscriptions=total_subs,
        )
 
        # s_night
        late_count, total_txn_count = await self.transaction_repo.get_late_night_non_essential_count(
            user_id, start, today, NON_ESSENTIAL_CATEGORIES
        )
        late_night_spending = sche_prs.LateNightSpending(
            late_night_non_essential_count=late_count,
            total_transaction_count=total_txn_count,
        )
 
        # s_pressure — thu chi trong kỳ lookback
        total_income   = await self.transaction_repo.get_monthly_income(user_id, start, today)
        total_expenses = await self.transaction_repo.get_all_spending(user_id, start, today)
        expense_pressure = sche_prs.ExpenseToIncomePressure(
            total_income=total_income,
            total_expenses=float(total_expenses),
        )
 
        prs = PeriodicRegretScore(
            impulse_spending=impulse_spending,
            budget_over_shoot=budget_overshoot,
            goal_disruption=goal_disruption,
            subscription_churn_signal=subscription_churn,
            late_night_spending=late_night_spending,
            expense_to_income_pressure=expense_pressure,
        )
        return prs.result()

    async def to_resilience(self, user_id: int, months: int = 4) -> dict:
        today            = date.today()
        begin_this_month = date(today.year, today.month, 1)

        # r_recovery — lấy toàn bộ transaction trong `months` tháng gần nhất
        months_ago = today.replace(day=1)
        for _ in range(months - 1):
            months_ago = (months_ago - timedelta(days=1)).replace(day=1)
        raw_txns = await self.transaction_repo.get_transactions_in_range(user_id, months_ago, today)
        monthly_income_avg = await self.transaction_repo.get_monthly_income(
            user_id, months_ago, today
        ) / months
        txns_for_recovery = [
            {
                "amount": float(t.amount) if t.category == "income" else -float(t.amount),
                "date":   t.date if isinstance(t.date, date) else t.date.date(),
            }
            for t in raw_txns
            if t.description != "INSUFFICIENT_BALANCE"
        ]
        balance_recovery = sche_resilience.BalanceRecoverySpeed(
            income=monthly_income_avg,
            txns=txns_for_recovery,
        )

        # r_goal
        monthly_goal_contributions = await self.transaction_repo.get_monthly_goal_contributions(
            user_id, months
        )
        goal_funding = sche_resilience.GoalFundingConsistency(
            monthly_goal_contributions=monthly_goal_contributions
        )

        # r_structure — tháng hiện tại
        essential_spending = await self.transaction_repo.get_essential_spending(
            user_id, begin_this_month, today, ESSENTIAL_CATEGORIES
        )
        total_spending = await self.transaction_repo.get_all_spending(
            user_id, begin_this_month, today
        )
        spending_structure = sche_resilience.SpendingStructure(
            essential_spending=essential_spending,
            total_spending=float(total_spending),
        )

        # r_entropy — phân bổ chi tiêu theo category tháng này
        spending_by_cat = await self.transaction_repo.get_spending_structure(
            user_id, begin_this_month, today
        )
        # Bỏ income ra khỏi entropy
        spending_by_cat_clean = {k: v for k, v in spending_by_cat.items() if k != "income"}
        spending_entropy = sche_resilience.SpendingEntropy(
            category_spending_amounts=spending_by_cat_clean
        )

        # r_adherence — overshoot từng category tháng này
        user = await self.user_repo.get_by_id(user_id)
        budget_map = {
            "food and drink": float(user.fad_budget or 0),
            "shopping":       float(user.shopping_budget or 0),
            "investment":     float(user.investment_budget or 0),
            "moving":         float(user.moving_budget or 0),
            "entertainment":  float(user.entertainment_budget or 0),
            "other":          float(user.other_budget or 0),
        }
        category_overshoots = await self.transaction_repo.get_category_overshoot_list(
            user_id, begin_this_month, today, budget_map
        )
        budget_adherence = sche_resilience.BudgetAdherence(
            category_overshoots=category_overshoots
        )

        # r_saving
        monthly_incomes   = await self.transaction_repo.get_monthly_income_list(user_id, months)
        monthly_expenses  = await self.transaction_repo.get_monthly_expense_list(user_id, months)
        savings_rate = sche_resilience.SavingsRateConsistency(
            monthly_income=monthly_incomes,
            monthly_expenses=monthly_expenses,
        )

        # r_income
        income_stability = sche_resilience.IncomeVolatilityAbsorption(
            monthly_income=monthly_incomes
        )

        resilience = ResilienceLevel(
            balance_recovery=balance_recovery,
            goal_funding=goal_funding,
            spending_structure=spending_structure,
            spending_entropy=spending_entropy,
            budget_adherence=budget_adherence,
            savings_rate=savings_rate,
            income_stability=income_stability,
        )
        return resilience.result()