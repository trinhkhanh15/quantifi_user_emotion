from pydantic import BaseModel, computed_field
from typing import Dict, List, Optional
from datetime import datetime, date

# Periodic Regret Score (PRS)

# =============================================================================
# COMPONENT A: Impulse Spending Score (S_impulse)
# =============================================================================
class ImpulseSpending(BaseModel):
    """
    What proportion of my spending is on non-essential items?
    
    S_impulse = 0.5 * (N_non_essential / N_total) + 0.5 * (sum_amt_non_essential / sum_amt_all)
    """
    non_essential_count: int  # Count of non-essential transactions
    total_count: int  # Total transaction count
    non_essential_amount: float  # Total amount of non-essential spending
    total_amount: float  # Total spending amount


# =============================================================================
# COMPONENT B: Budget Overshoot Score (S_budget)
# =============================================================================
class BudgetOvershoot(BaseModel):
    """
    How much did I overshoot my budget across categories?
    
    Công thức cũ: sigmoid(2 * mean) → khi mean=0 vẫn cho 0.5 (BUG).
    Fix: 2*sigmoid(3*mean) - 1, clamp [0,1] → = 0 khi không vượt budget.
    """
    category_overshoots: List[float]  # List of overshoot ratios per category
    # Overshoot ratio = max(0, (spent - budget) / budget) for each category


# =============================================================================
# COMPONENT C: Goal Disruption Score (S_goal)
# =============================================================================
class GoalDisruption(BaseModel):
    """
    How much did my spending jeopardize my financial goals?
    
    S_goal = (1/G) * sum[0.6 * min(spend/remaining, 1) + 0.4 * sigmoid((days_now/days_cf) - 1)]
    """
    goals_data: List[Dict]  # List of goal data dictionaries containing:
    # - target_amount: float
    # - current_amount: float
    # - end_date: date
    # - spending_toward_goal: float (non-goal spending in the period that competes with this goal)


# =============================================================================
# COMPONENT D: Subscription Churn Signal (S_sub)
# =============================================================================
class SubscriptionChurnSignal(BaseModel):
    """
    Have I been cancelling subscriptions recently?
    
    S_sub = min(N_cancelled_last_14d / N_total_subs, 1.0)
    """
    cancelled_subscriptions_14d: int  # Count of cancelled subs in last 14 days
    total_subscriptions: int  # Total subscription count


# =============================================================================
# COMPONENT E: Late-Night Spending Ratio (S_night)
# =============================================================================
class LateNightSpending(BaseModel):
    """
    What proportion of my recent spending happened late at night on non-essentials?
    
    S_night = N_late_night_non_essential / N_recent
    
    Late night: 23:00 - 05:00
    """
    late_night_non_essential_count: int  # Late-night non-essential transactions
    total_transaction_count: int  # Total recent transactions


# =============================================================================
# COMPONENT F: Expense-to-Income Pressure (S_pressure)
# =============================================================================
class ExpenseToIncomePressure(BaseModel):
    """
    Am I spending a large proportion of my income?
    
    S_pressure = sigmoid(3 * (E_month / I_month - 0.7))
    
    Where E_month is total expenses and I_month is total income
    """
    total_income: float  # Sum of income transactions in period
    total_expenses: float  # Sum of expense transactions in period


# =============================================================================
# PRS MASTER FORMULA - Weighted Combination
# =============================================================================
class PeriodicRegretScore(BaseModel):
    """
    Master formula combining all components with weights:
    
    PRS = sigmoid(α1*S_impulse + α2*S_budget + α3*S_goal + α4*S_sub + α5*S_night + α6*S_pressure - β)
    
    Default Weights:
    - α1 (Impulse Spending): 2.0
    - α2 (Budget Overshoot): 2.5
    - α3 (Goal Disruption): 3.0
    - α4 (Subscription Churn): 1.5
    - α5 (Late-Night Spending): 1.0
    - α6 (Expense Pressure): 2.0
    
    Centering bias (β): 3.5
    """
    # Component scores (0-1 range)
    s_impulse: Optional[float] = None
    s_budget: Optional[float] = None
    s_goal: Optional[float] = None
    s_sub: Optional[float] = None
    s_night: Optional[float] = None
    s_pressure: Optional[float] = None
    
    # Default weights
    DEFAULT_WEIGHTS: Dict[str, float] = {
        "alpha1_impulse": 2.0,
        "alpha2_budget": 2.5,
        "alpha3_goal": 3.0,
        "alpha4_sub": 1.5,
        "alpha5_night": 1.0,
        "alpha6_pressure": 2.0,
    }
    
    # Centering bias: 3.5 → 3.0 sau khi fix S_budget và S_goal
    # Với formula cũ, S_budget có floor 0.5 và S_goal có floor 0.2 → inflate score
    # Sau fix cả hai về 0 khi không có vấn đề, beta=3.0 giữ nguyên calibration
    # theo spec scenarios (impulse≈0.895, paycheck≈0.572, healthy≈0.069)
    beta: float = 3.0
    
    @staticmethod
    def sigmoid(x: float) -> float:
        """Sigmoid activation function"""
        import math
        try:
            return 1.0 / (1.0 + math.exp(-max(-20, min(20, x))))
        except:
            return 0.5 if x == 0 else (1.0 if x > 0 else 0.0)
    
    @computed_field
    @property
    def final_score(self) -> float:
        """Calculate final PRS with sigmoid"""
        w = self.DEFAULT_WEIGHTS
        weighted_sum = (
            w["alpha1_impulse"] * (self.s_impulse or 0) +
            w["alpha2_budget"] * (self.s_budget or 0) +
            w["alpha3_goal"] * (self.s_goal or 0) +
            w["alpha4_sub"] * (self.s_sub or 0) +
            w["alpha5_night"] * (self.s_night or 0) +
            w["alpha6_pressure"] * (self.s_pressure or 0) -
            self.beta
        )
        return self.sigmoid(weighted_sum)