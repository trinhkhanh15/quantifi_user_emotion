# FinanceFeel — Know How You'll Feel Before You Spend

---

## 1. Problem

Every day, millions of people make purchases they immediately regret.

They overspend on impulse. They blow past their own budgets. They wake up the next morning and realize their savings goal just got pushed back another month. Financial apps show them *what* they spent — but never warn them *before* they spend, and never tell them *how they'll feel after*.

The result? Guilt, stress, and a quiet erosion of financial confidence that compounds over time.

---

## 2. Key Insight

Current fintech tools are **rearview mirrors**. They categorize your past, judge your present, and leave you alone with the consequences.

They ask you to fill out income surveys. They demand you set up complicated budgets. They lecture you after the damage is done.

What people actually need is a **co-pilot** — something that reads the behavioral patterns already hidden in their transactions, and speaks up *before* the regret hits.

---

## 3. Solution Overview

**FinanceFeel** is an AI behavioral finance layer that predicts two emotional scores in real time — directly from a user's existing transaction data:

- **Regret Score** — how likely you are to regret this spending pattern
- **Resilience Score** — how well you'll recover if you do spend

No surveys. No manual input. No income forms. Everything is computed automatically, invisibly, and instantly.

---

## 4. Core Innovation

Most finance AIs optimize for *numbers*. We optimize for *feelings*.

We model the **emotional consequence of financial behavior** using five regret signals and five resilience signals derived entirely from transaction data — impulse bursts, late-night purchases, goal disruption velocity, subscription churn, and budget drift.

The result is a living emotional fingerprint of your financial health. Not a score from the past. A **prediction about how you'll feel tomorrow**.

---

## 5. How It Works

Think of it like a weather forecast — but for your wallet.

When you're about to make a purchase, FinanceFeel already knows:
- You've been on a shopping streak for 3 days
- You cancelled a subscription 5 days ago
- Your savings goal deadline is 3 weeks away
- You bought something similar at 2 AM last Tuesday and returned it

It combines all of that into a single human signal: *"Heads up — your Regret Score is high right now."*

---

## 6. User Experience

FinanceFeel integrates directly into any fintech app as a lightweight behavioral layer.

Users see:
- A **daily emotional snapshot** — their Regret and Resilience scores at a glance
- **Real-time nudges** before high-risk transactions
- **Weekly insight cards** — *"You recover fastest after food spending. Entertainment takes you 12 days."*
- **Streak rewards** for resilience-positive behaviors

This creates a natural daily check-in loop — not because we ask users to open the app, but because the insights are genuinely personal, surprising, and useful.

---

## 7. Impact

Financial regret isn't just uncomfortable — it's a gateway to anxiety, avoidance, and long-term disengagement from personal finance.

FinanceFeel turns that cycle around. Users who understand their behavioral patterns make fewer impulsive decisions, recover faster from financial shocks, and build stronger goal discipline — without being lectured or shamed.

**Better financial behavior. Less financial stress. More people in control of their future.**

---

## 8. Scalability

FinanceFeel is built to grow — and every part of the architecture accelerates that growth.

Because the system runs entirely on transaction data that banks and fintechs already collect, **onboarding a new user costs nothing extra**. No surveys, no setup, no cold start. The moment a user has transaction history, FinanceFeel works for them — whether they're a student with 20 transactions or a professional with 2,000.

More users means more behavioral patterns. More patterns means a sharper fine-tuned model. A sharper model means more accurate, more personal nudges — which drives higher engagement, which brings more users. **It's a compounding flywheel, not a linear growth curve.**

And because the scoring API is stateless and hosted on AWS, scaling from 10,000 to 10 million users is an infrastructure dial, not an engineering rewrite. The system is equally at home powering a neobank in Vietnam or a super-app in Southeast Asia — the behavioral signals are universal, the language of money is the same everywhere.

---

## 9. Integration Potential

FinanceFeel is designed as a **plug-in behavioral intelligence API** — drop it into any existing fintech, neobank, or mobility super-app.

Imagine: a ride-hailing app that nudges you before an impulse upgrade. A BNPL platform that shows your Regret Score before you split a payment. A savings app that celebrates your Resilience streak.

The behavioral layer is universal. The integration is seamless.

---

## 10. Technical Signals

### Immediate Regret Score (IRS) — Real-Time Transaction Risk

$$\text{IRS} = \sigma\!\left(4.5 \cdot \text{raw} - 2.0\right)$$

where

$$\text{raw} = \min\left(1.5,\, (\text{linear} + \text{penalty}) \cdot \text{amplifier}\right)$$

**Linear Component:** Weighted sum of 8 signals
$$\text{linear} = 0.208 \cdot S_{\text{budget}} + 0.189 \cdot S_{\text{income}} + 0.094 \cdot S_{\text{time}} + 0.189 \cdot S_{\text{goal}} + 0.123 \cdot S_{\text{freq}} + 0.085 \cdot S_{\text{cat}} + 0.066 \cdot S_{\text{dom}} + 0.047 \cdot S_{\text{vel}}$$

**Convergence Penalty:** Non-linear amplification when $N \geq 2$ signals are active simultaneously
$$\text{penalty} = \min(0.35,\, 0.04 \cdot N^{1.6})$$

**Interaction Amplifiers:** 5 behavioral feedback loops
$$\text{amplifier} = 1.0 + 0.25 \cdot S_{\text{time}} \cdot S_{\text{vel}} + 0.35 \cdot S_{\text{budget}} \cdot S_{\text{goal}} + 0.20 \cdot S_{\text{freq}} \cdot S_{\text{cat}} + 0.18 \cdot S_{\text{dom}} \cdot S_{\text{budget}} + 0.15 \cdot S_{\text{time}} \cdot S_{\text{income}}$$

| Signal | Purpose | Formula |
|---|---|---|
| $S_{\text{budget}}$ | Budget breach severity | `min(1, max(0, (spent_month + txn - budget) / budget))` |
| $S_{\text{income}}$ | Transaction shock relative to income | `min(1, (txn / income)^0.7)` |
| $S_{\text{time}}$ | Late-night vulnerability | Piecewise: `0.0` (6–21h), `0.3` (21–23h), `0.7` (23–1h), `1.0` (1–5h), `0.5` (5–6h) |
| $S_{\text{goal}}$ | Goal conflict severity | `min(1, (txn / remaining) * (30 / days_left))` |
| $S_{\text{freq}}$ | Category frequency anomaly | `min(1, max(0, (recent_count - baseline) / baseline))` |
| $S_{\text{cat}}$ | Category risk profile | Lookup table (Groceries: 0.00 → Gambling: 0.90) |
| $S_{\text{dom}}$ | Day-of-month timing | `max(0, month_remaining_ratio - budget_remaining_ratio)` |
| $S_{\text{vel}}$ | Spending velocity (spree detection) | `min(1, (txns_2h / 5) * 0.5 + (amount_2h / daily_budget) * 0.5)` |

---

### Periodic Regret Score (PRS) — Weekly/Monthly Pattern Review

$$\text{PRS} = \sigma\!\left(2.0 \cdot S_{\text{impulse}} + 2.5 \cdot S_{\text{budget}} + 3.0 \cdot S_{\text{goal}} + 1.5 \cdot S_{\text{sub}} + 1.0 \cdot S_{\text{night}} + 2.0 \cdot S_{\text{pressure}} - 3.0\right)$$

| Signal | Purpose | Formula |
|---|---|---|
| $S_{\text{impulse}}$ | Impulse spending ratio | `0.5 * (non_essential_count / total_count) + 0.5 * (non_essential_amt / total_amt)` |
| $S_{\text{budget}}$ | Budget overshoot across categories | `2 * sigmoid(3 * mean_overshoot) - 1`, clamped to `[0, 1]` |
| $S_{\text{goal}}$ | Goal disruption severity | `(1/G) * sum[0.6 * min(spend/remaining, 1) + 0.4 * sigmoid((days_now/days_cf) - 1)]` |
| $S_{\text{sub}}$ | Subscription churn signal | `min(cancelled_14d / total_subs, 1)` |
| $S_{\text{night}}$ | Late-night spending ratio | `(late_night_non_ess_count / recent_count)` |
| $S_{\text{pressure}}$ | Expense-to-income pressure | `sigmoid(3 * (expenses / income - 0.7))` |

---

### Resilience Score — Financial Recovery & Stability

$$\text{Resilience} = \sigma\!\left(1.75 \cdot R_{\text{recovery}} + 2.10 \cdot R_{\text{goal}} + 1.05 \cdot R_{\text{structure}} + 0.70 \cdot R_{\text{entropy}} + 1.40 \cdot R_{\text{adherence}} + 1.75 \cdot R_{\text{saving}} + 1.05 \cdot R_{\text{income}} - 5.5\right)$$

| Signal | Purpose | Formula |
|---|---|---|
| $R_{\text{recovery}}$ | Balance recovery speed after shocks | $\frac{1}{\|S\|} \sum_{s} e^{-0.05 \cdot d_s}$ where $d_s$ = days since balance dip, S = set of dips |
| $R_{\text{goal}}$ | Goal funding consistency | `0.6 * exp(-CV) + 0.4 * (active_months / total_months)` |
| $R_{\text{structure}}$ | Spending structure sustainability | `exp(-(r - 0.6)^2 / 0.08)` where `r = essential / total` (peak at 60% essential spending) |
| $R_{\text{entropy}}$ | Spending diversification | `H(p) / ln(K)` where `H(p) = -sum(p_i * ln(p_i))` (Shannon entropy of category distribution) |
| $R_{\text{adherence}}$ | Budget adherence consistency | `(1/K) * sum(exp(-max(0, overshoot_i)))` where `overshoot_i = (spent_i - budget_i) / budget_i` |
| $R_{\text{saving}}$ | Savings rate consistency | `0.5 * sigmoid(5 * avg_rate) + 0.5 * exp(-2 * std_rate)` |
| $R_{\text{income}}$ | Income volatility absorption | `exp(-1.5 * CV_income)` (coefficient of variation of monthly income) |

---

## 11. Tech Stack & Build Process

### How We Built It

```
User Transaction Data
        │
        ▼
┌───────────────────┐
│   PostgreSQL DB   │  ← Stores transactions, goals, subscriptions, budgets
└────────┬──────────┘
         │ SQLAlchemy ORM queries
         ▼
┌───────────────────┐
│  FastAPI Backend  │  ← Computes behavioral signals, exposes REST endpoints
└────────┬──────────┘
         │ Fine-tuned model inference
         ▼
┌───────────────────┐
│   AWS (Fine-tuned │  ← Hosts our fine-tuned model for score prediction
│   Model Endpoint) │     and personalized nudge generation
└────────┬──────────┘
         │ JSON response
         ▼
┌───────────────────┐
│   React Frontend  │  ← Renders Regret / Resilience scores, nudges, insights
└───────────────────┘
```

### Technology Choices & Rationale

| Layer | Technology | Why We Chose It |
|---|---|---|
| **Database** | PostgreSQL | Relational integrity for linked transactions, goals, and subscriptions. Enables complex aggregation queries across time windows without schema changes. |
| **ORM** | SQLAlchemy | All behavioral signals are computed as virtual properties on top of existing schema — no new tables, no migrations needed. |
| **Backend API** | FastAPI (Python) | Async-first, automatically typed, and ideal for serving real-time score computation endpoints with minimal latency. Python also natively supports NumPy for signal math. |
| **AI Model** | Fine-tuned model on AWS | We fine-tuned a base model on behavioral finance patterns to generate contextual, personalized nudges — not generic advice. Hosted on AWS for low-latency inference, scalability, and production reliability. |
| **Frontend** | React | Component-based architecture allows the Regret/Resilience scores, nudge cards, and insight dashboards to update reactively without full page reloads — critical for a daily-engagement product. |

### Key Engineering Decisions

- **Formula-first, model-assisted** — The Regret and Resilience scores are computed deterministically via weighted sigmoid formulas. The fine-tuned model is used on top to generate human-readable explanations and nudges, keeping the core scoring transparent and auditable.
- **No new data required** — Every signal is derived from relationships already present in the database. The system activates instantly for any existing user.
- **Stateless API design** — Each scoring request is self-contained, making the backend horizontally scalable on AWS without session or state management overhead.

---

## 12. Dataset

### Built From Simulated Reality

One of the most honest challenges in behavioral finance AI is data. Real transaction data is private, regulated, and hard to access — especially at a hackathon. So we made a deliberate engineering choice: **we simulated it**.

Our dataset was constructed by modeling how real users actually behave — not just random numbers, but grounded behavioral archetypes:

| User Profile | Behavior Simulated |
|---|---|
| The Impulse Shopper | Frequent non-essential bursts, late-night purchases, occasional subscription cancellations |
| The Disciplined Saver | Consistent goal contributions, low budget deviation, fast shock recovery |
| The Stressed but Recovering | Moderate overspending, missed goal months, gradual self-correction |

Each profile drives transaction patterns across categories, time-of-day distributions, goal funding cadences, and subscription lifecycles — producing a dataset that reflects the *variance* of real human financial behavior, not just its average.

### Why Simulation Is a Valid Starting Point

Simulation lets us stress-test the scoring model against known ground truth. We know exactly what each user "should" score, which lets us validate that the formulas behave correctly before touching real data. It's the same approach used in clinical trials — synthetic cohorts before live patients.

The trade-off is coverage. Simulated data captures the behavioral patterns we explicitly designed for. Real-world data would surface edge cases we haven't imagined yet — irregular income, cross-border spending, generational habits, cultural spending norms.

### The Path to Production Accuracy

The architecture is already built for this transition:

```
Simulated Dataset (now)
        │
        ▼  Fine-tuning improves with more patterns
Anonymized Real Transaction Data (next)
        │
        ▼  Feedback loop from behavioral proxy labels
Self-Improving Model on AWS (scale)
```

As the user base grows, every transaction becomes a new data point. Every regret signal confirmed by a real behavioral proxy — a refund, a cancellation, a spending freeze — tightens the model's calibration. **The dataset is not a limitation. It is the foundation we scale from.**

---

## 13. Closing Statement

We don't just track money. We track the *human* behind the money.

FinanceFeel is the first system that predicts how you'll feel about your financial decisions — before you make them. It doesn't replace your willpower. It quietly shows up for you when your willpower is running low.

**Because the best financial advice isn't a budget. It's self-awareness, delivered at the right moment.**

---

*Built on behavioral economics. Powered by transaction data. Designed for the way people actually live.*
