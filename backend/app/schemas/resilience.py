from pydantic import BaseModel, computed_field
from typing import Dict, List, Optional
from datetime import datetime, date

# Resilience Score

# =============================================================================
# COMPONENT A: Balance Recovery Speed (R_recovery)
# =============================================================================
class BalanceRecoverySpeed(BaseModel):
    """
    How quickly am I recovering balance after a dip?
    
    R_recovery = (1/|S|) * sum(exp(-0.05 * d_s))
    
    Where d_s is days since last dip, weighted exponentially
    """
    income: float
    txns: List[Dict]  # List of transactions with their details


# =============================================================================
# COMPONENT B: Goal Funding Consistency (R_goal)
# =============================================================================
class GoalFundingConsistency(BaseModel):
    """
    How consistently am I funding my financial goals?
    
    R_goal = 0.6 * exp(-CV) + 0.4 * (N_active_months / N_total_months)
    
    Where CV is coefficient of variation of goal contributions
    """
    monthly_goal_contributions: List[float]  # Goal contributions per month


# =============================================================================
# COMPONENT C: Spending Structure (R_structure)
# =============================================================================
class SpendingStructure(BaseModel):
    """
    How stable is my spending distribution across categories?
    
    R_structure = exp(-(r - 0.6)^2 / 0.08)
    
    Where r is ratio of essential to total spending (ideally 0.6)
    """
    essential_spending: float  # Amount spent on essential categories
    total_spending: float  # Total spending


# =============================================================================
# COMPONENT D: Spending Entropy (R_entropy)
# =============================================================================
class SpendingEntropy(BaseModel):
    """
    How diversified is my spending across categories?
    
    R_entropy = H(p) / ln(K)
    
    Where H is Shannon entropy and K is number of categories
    """
    category_spending_amounts: Dict[str, float]  # Raw spending amount per category (normalized internally)


# =============================================================================
# COMPONENT E: Budget Adherence (R_adherence)
# =============================================================================
class BudgetAdherence(BaseModel):
    """
    How consistently do I stay within my budget?
    
    R_adherence = (1/K) * sum(exp(-max(0, δ_i)))
    
    Where δ_i is overshoot ratio for each category
    """
    category_overshoots: List[float]  # Overshoot ratios per category
    # Overshoot δ_i = max(0, (spent_i - budget_i) / budget_i)


# =============================================================================
# COMPONENT F: Savings Rate Consistency (R_savings)
# =============================================================================
class SavingsRateConsistency(BaseModel):
    """
    How consistent is my saving behavior?
    
    R_savings = 0.5 * sigmoid(5 * avg_rate) + 0.5 * exp(-2 * std_rate)
    
    Where avg_rate is average monthly savings rate: (I_m - E_m) / I_m
    And std_rate is standard deviation of monthly savings rates
    """
    monthly_income: List[float]  # Monthly income values
    monthly_expenses: List[float]  # Monthly expense values


# =============================================================================
# COMPONENT G: Income Volatility Absorption (R_income_stability)
# =============================================================================
class IncomeVolatilityAbsorption(BaseModel):
    """
    How stable is my income and can I absorb variability?
    
    R_income_stability = exp(-1.5 * CV_income)
    
    Where CV_income = σ_I / μ_I (coefficient of variation of income)
    """
    monthly_income: List[float]  # Monthly income values
    # CV is calculated internally from these values


# =============================================================================
# RESILIENCE MASTER FORMULA - Weighted Combination
# =============================================================================
class ResilienceScore(BaseModel):
    """
    Master formula combining all components with weights:
    
    Resilience = sigmoid(β1*R_recovery + β2*R_goal + β3*R_structure + β4*R_entropy + β5*R_adherence + β6*R_savings + β7*R_income_stability - δ)
    
    Default Weights:
    - β1 (Balance Recovery): 2.5
    - β2 (Goal Funding): 3.0
    - β3 (Spending Structure): 1.5
    - β4 (Spending Entropy): 1.0
    - β5 (Budget Adherence): 2.0
    - β6 (Savings Rate): 2.5
    - β7 (Income Stability): 1.5
    
    Centering bias (δ): 5.0
    """
    # Component scores (0-1 range)
    r_recovery: Optional[float] = None
    r_goal: Optional[float] = None
    r_structure: Optional[float] = None
    r_entropy: Optional[float] = None
    r_adherence: Optional[float] = None
    r_saving: Optional[float] = None
    r_income: Optional[float] = None
    
    # Default weights
    DEFAULT_WEIGHTS: Dict[str, float] = {
        "beta1_recovery": 1.75,
        "beta2_goal": 2.10,
        "beta3_structure": 1.05,
        "beta4_entropy": 0.70,
        "beta5_adherence": 1.40,
        "beta6_savings": 1.75,
        "beta7_income_stability": 1.05,
    }
    
    # Centering bias: 5.5 (calibrated after bug fixes)
    # Bug fixes: r_entropy không còn âm, r_adherence=0 khi no budget, r_recovery không default 1.0
    # delta=5.5 → neutral khi avg_component ≈ 5.5/9.8 = 0.56
    # Expected: disciplined≈0.96, average≈0.67, no_budget≈0.52, impulse≈0.13, struggling≈0.05
    delta: float = 5.5

    
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
        """Calculate final Resilience score with sigmoid"""
        w = self.DEFAULT_WEIGHTS
        weighted_sum = (
            w["beta1_recovery"] * (self.r_recovery or 0) +
            w["beta2_goal"] * (self.r_goal or 0) +
            w["beta3_structure"] * (self.r_structure or 0) +
            w["beta4_entropy"] * (self.r_entropy or 0) +
            w["beta5_adherence"] * (self.r_adherence or 0) +
            w["beta6_savings"] * (self.r_saving or 0) +
            w["beta7_income_stability"] * (self.r_income or 0) -
            self.delta
        )
        return self.sigmoid(weighted_sum)