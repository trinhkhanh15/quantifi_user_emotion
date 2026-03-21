from pydantic import BaseModel, computed_field
from typing import Dict, List, Optional
from datetime import date, datetime

# Immediate Regret Score (IRS)

# =============================================================================
# COMPONENT A: Budget Breach Ratio (S_budget)
# =============================================================================
class BudgetBreach(BaseModel):
    """
    How much does this transaction push me over my category budget?
    
    S_budget = min(1, max(0, (category_spent_this_month + txn_amount - category_budget) / category_budget))
    """
    category_budget: float
    category_spent: float
    txn_amount: float


# =============================================================================
# COMPONENT B: Income Proportion Shock (S_income)
# =============================================================================
class IncomeProportionShock(BaseModel):
    """
    How large is this single purchase relative to my income?
    
    S_income = min(1, (txn_amount / monthly_income)^0.7)
    """
    txn_amount: float
    monthly_income: float


# =============================================================================
# COMPONENT C: Temporal Vulnerability (S_time)
# =============================================================================
class TemporalVulnerability(BaseModel):
    """
    Am I making this purchase at a time associated with impulsive behavior?
    
    S_time = 0.0  if 6:00 <= t < 21:00
           = 0.3  if 21:00 <= t < 23:00
           = 0.7  if 23:00 <= t < 1:00
           = 1.0  if 1:00 <= t < 5:00
           = 0.5  if 5:00 <= t < 6:00
    """
    txn_datetime: datetime


# =============================================================================
# COMPONENT D: Goal Conflict Severity (S_goal)
# =============================================================================
class GoalConflictSeverity(BaseModel):
    """
    Does this purchase directly jeopardize a financial goal I've set?
    
    Simplified: S_goal = min(1, (txn_amount / remaining_needed) * (30 / max(days_left, 1)))
    """
    goals_data: List[Dict]  # List of goal data dictionaries containing:
    # - target_amount: float
    # - current_amount: float
    # - end_date: date
    txn_amount: float


# =============================================================================
# COMPONENT E: Category Frequency Anomaly (S_freq)
# =============================================================================
class CategoryFrequencyAnomaly(BaseModel):
    """
    Have I been spending abnormally often in this category recently?
    
    S_freq = min(1, max(0, (recent_count - baseline_weekly_count) / max(baseline_weekly_count, 1)))
    """
    recent_count: float  # Count of transactions in same category in last 7 days
    baseline_weekly_count: float  # Count of transactions in same category in last 90 days


# =============================================================================
# COMPONENT F: Category Risk Profile (S_cat)
# =============================================================================
class CategoryRiskProfile(BaseModel):
    """
    Is this category historically associated with regret?
    
    Static lookup table for category risk scores:
    - Groceries / Utilities: 0.00
    - Transportation (commute): 0.05
    - Dining out: 0.20
    - Entertainment / Streaming: 0.25
    - Fast Fashion / Apparel: 0.45
    - Online Shopping (general): 0.40
    - Food Delivery: 0.50
    - In-App Purchases / Gaming: 0.70
    - Gambling / Lottery: 0.90
    - Alcohol / Tobacco: 0.60
    """
    category: str
    
    # Risk scores by category
    CATEGORY_RISK_SCORES: Dict[str, float] = {
        "groceries": 0.00,
        "utilities": 0.00,
        "transportation": 0.05,
        "transport": 0.05,
        "dining_out": 0.20,
        "dining": 0.20,
        "restaurant": 0.20,
        "entertainment": 0.25,
        "streaming": 0.25,
        "fast_fashion": 0.45,
        "apparel": 0.45,
        "clothing": 0.45,
        "online_shopping": 0.40,
        "shopping": 0.40,
        "food_delivery": 0.50,
        "delivery": 0.50,
        "in_app_purchases": 0.70,
        "gaming": 0.70,
        "gambling": 0.90,
        "lottery": 0.90,
        "alcohol": 0.60,
        "tobacco": 0.60,
        "vice": 0.60,
    }
    
    @property
    def risk_score(self) -> float:
        return self.CATEGORY_RISK_SCORES.get(self.category.lower(), 0.25)  # Default moderate risk


# =============================================================================
# COMPONENT G: Day-of-Month Timing (S_dom)
# =============================================================================
class DayOfMonthTiming(BaseModel):
    """
    Am I spending at the end of the month when money is tight?
    
    S_dom = max(0, month_remaining_ratio - budget_remaining_ratio)
    """
    monthly_budget: float
    total_spent: float


# =============================================================================
# COMPONENT H: Spending Velocity (S_vel)
# =============================================================================
class SpendingVelocity(BaseModel):
    """
    Am I on a spending spree right now?
    
    S_vel = min(1, (txns_last_2h / 5) * 0.5 + (amount_last_2h / daily_budget) * 0.5)
    """
    txns_last_2h: int
    amount_last_2h: float
    daily_budget: float


# =============================================================================
# IRS MASTER FORMULA - Weighted Combination
# =============================================================================
class ImmediateRegretScore(BaseModel):
    """
    Master formula combining all components with weights:
    
    IRS = w1*S_budget + w2*S_income + w3*S_time + w4*S_goal + w5*S_freq + w6*S_cat + w7*S_dom + w8*S_vel
    
    Default Weights:
    - w1 (Budget Breach): 0.25
    - w2 (Income Shock): 0.20
    - w3 (Night Time): 0.08
    - w4 (Goal Conflict): 0.18
    - w5 (Frequency Anomaly): 0.10
    - w6 (Category Risk): 0.07
    - w7 (Day-of-Month): 0.07
    - w8 (Spending Velocity): 0.05
    """
    # Component scores (0-1 range)
    s_budget: Optional[float] = None
    s_income: Optional[float] = None
    s_time: Optional[float] = None
    s_goal: Optional[float] = None
    s_freq: Optional[float] = None
    s_cat: Optional[float] = None
    s_dom: Optional[float] = None
    s_vel: Optional[float] = None
    
    # Default weights — V3 (Weather Forecast Model)
    # Điều chỉnh từ V2: goal +0.02, freq +0.03, time +0.02, cat +0.02, budget -0.04
    # Rationale: temporal/frequency signals underweighted, goal conflict cần mạnh hơn
    DEFAULT_WEIGHTS: Dict[str, float] = {
        "w1_budget": 0.208,
        "w2_income": 0.189,
        "w3_time":   0.094,
        "w4_goal":   0.189,
        "w5_freq":   0.123,
        "w6_cat":    0.085,
        "w7_dom":    0.066,
        "w8_vel":    0.047,
    }
 
    # Signal thresholds — dùng để đếm "active signals" cho convergence penalty
    SIGNAL_THRESHOLDS: Dict[str, float] = {
        "s_budget": 0.30,
        "s_income": 0.25,
        "s_goal":   0.30,
        "s_freq":   0.35,
        "s_time":   0.30,
        "s_cat":    0.35,
        "s_dom":    0.25,
        "s_vel":    0.35,
    }
 
    # Interaction amplifiers — V3: 5 pairs thay vì 2
    # α1: late-night + spending spree
    # α2: over-budget + goal threatened (giữ từ V2, giảm nhẹ)
    # α3: frequency anomaly + risky category (MỚI)
    # α4: month-end squeeze + budget breach (MỚI)
    # α5: late-night + large amount (MỚI — impulse at night amplifier)
    alpha1: float = 0.25   # time * vel
    alpha2: float = 0.35   # budget * goal
    alpha3: float = 0.20   # freq * cat
    alpha4: float = 0.18   # dom * budget
    alpha5: float = 0.15   # time * income
    
    @property
    def linear_score(self) -> float:
        """Calculate linear weighted sum"""
        w = self.DEFAULT_WEIGHTS
        score = (
            w["w1_budget"] * (self.s_budget or 0) +
            w["w2_income"] * (self.s_income or 0) +
            w["w3_time"]   * (self.s_time   or 0) +
            w["w4_goal"]   * (self.s_goal   or 0) +
            w["w5_freq"]   * (self.s_freq   or 0) +
            w["w6_cat"]    * (self.s_cat    or 0) +
            w["w7_dom"]    * (self.s_dom    or 0) +
            w["w8_vel"]    * (self.s_vel    or 0)
        )
        return min(1.0, score)
 
    @property
    def convergence_penalty(self) -> float:
        """
        Weather-forecast style: N active signals simultaneously = non-linear penalty.
        Đếm số signal vượt ngưỡng → penalty tăng theo N^1.6.
        1 signal = 0, 2 signals = +0.12, 4 signals = +0.35 (capped).
        """
        components = {
            "s_budget": self.s_budget or 0,
            "s_income": self.s_income or 0,
            "s_goal":   self.s_goal   or 0,
            "s_freq":   self.s_freq   or 0,
            "s_time":   self.s_time   or 0,
            "s_cat":    self.s_cat    or 0,
            "s_dom":    self.s_dom    or 0,
            "s_vel":    self.s_vel    or 0,
        }
        active = sum(
            1 for k, v in components.items()
            if v >= self.SIGNAL_THRESHOLDS.get(k, 0.30)
        )
        if active <= 1:
            return 0.0
        return min(0.35, 0.04 * (active ** 1.6))
 
    @computed_field
    @property
    def final_score(self) -> float:
        """
        IRS V3 — Weather Forecast Model.
 
        3 layers:
          L1: weighted linear sum (component scores × weights)
          L2: convergence penalty (N active signals simultaneously → non-linear boost)
          L3: 5 interaction amplifiers + calibrated sigmoid transform
 
        Sigmoid transform: maps [0, ∞) → [0, 1] mượt hơn hard clamp.
        floor tại x=0 = 0 → giao dịch hoàn toàn lành mạnh cho IRS ≈ 0.
        """
        import math
        _sigmoid = lambda x: 1.0 / (1.0 + math.exp(-max(-20, min(20, x))))
 
        linear  = self.linear_score
        penalty = self.convergence_penalty
 
        # Interaction amplifiers (5 pairs)
        amplifier = 1.0
        s_time   = self.s_time   or 0
        s_vel    = self.s_vel    or 0
        s_budget = self.s_budget or 0
        s_goal   = self.s_goal   or 0
        s_freq   = self.s_freq   or 0
        s_cat    = self.s_cat    or 0
        s_dom    = self.s_dom    or 0
        s_income = self.s_income or 0
 
        amplifier += self.alpha1 * s_time   * s_vel     # late-night spree
        amplifier += self.alpha2 * s_budget * s_goal    # budget + goal double threat
        amplifier += self.alpha3 * s_freq   * s_cat     # anomalous freq in risky category
        amplifier += self.alpha4 * s_dom    * s_budget  # month-end + over-budget
        amplifier += self.alpha5 * s_time   * s_income  # large amount at night
 
        raw = min(1.5, (linear + penalty) * amplifier)
 
        # Calibrated sigmoid: floor=0 at x=0, reaches ~0.91 at x=1.0
        floor = _sigmoid(-2.0)
        score = (_sigmoid(4.5 * raw - 2.0) - floor) / (1.0 - floor + 1e-8)
        return round(max(0.0, min(1.0, score)), 6)