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

'''
========================================================================================================================
| NOTE: Core calculation logic is redacted in the public repository to protect proprietary financial behavioral models.|
========================================================================================================================
'''

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
        pass

    def calculate_s_income(self):
        pass

    def calculate_s_time(self):
        pass

    def calculate_s_goal(self):
        pass

    def calculate_s_frequency(self):
        pass

    def calculate_s_category_risk(self):
        pass

    def calculate_s_day_of_month(self):
        pass

    def calculate_s_spending_velocity(self):
        pass
    
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
        pass
 
    def calculate_s_budget(self):
        pass
    
    def calculate_s_goal(self):
        pass

    def calculate_s_subscription(self):
        pass
 
    def calculate_s_night(self):
        pass
 
    def calculate_s_pressure(self):
        pass
    
    def result(self):
        pass
    
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
        pass

    def calculate_r_goal(self):
        pass
    
    def calculate_r_structure(self):
        pass
    
    def calculate_r_entropy(self):
        pass
    
    def calculate_r_adherence(self):
        pass
    
    def calculate_r_saving(self):
        pass

    def calculate_r_income(self):
        pass

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
        pass

    async def to_prs(self, user_id: int, lookback_days: int = 14) -> dict:
        pass

    async def to_resilience(self, user_id: int, months: int = 4) -> dict:
        pass