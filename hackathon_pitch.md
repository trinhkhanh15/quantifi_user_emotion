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

### Regret Score

$$\text{Regret} = \sigma\!\left(2.0\,S_{\text{impulse}} + 2.5\,S_{\text{budget}} + 3.0\,S_{\text{goal}} + 1.5\,S_{\text{sub}} + 1.0\,S_{\text{night}} - 3.0\right)$$

| Signal | Formula | Why It Causes Regret |
|---|---|---|
| $S_{\text{impulse}}$ | $0.5\cdot\dfrac{N_{\text{non-essential}}}{N_{\text{total}}} + 0.5\cdot\dfrac{\sum\text{amt}_{\text{non-essential}}}{\sum\text{amt}_{\text{all}}}$ | Impulse purchases bypass rational decision-making. Once the excitement fades, users perceive the gap between reward received and cost paid — triggering counterfactual regret. |
| $S_{\text{budget}}$ | $\sigma\!\left(2\cdot\dfrac{1}{K}\sum\max\!\left(0,\,\dfrac{\text{spent}_i - \text{budget}_i}{\text{budget}_i}\right)\right)$ | Budgets are self-imposed commitment devices. Breaking them triggers a "broken promise" effect — users shift from *"I'm in control"* to *"I failed my own plan."* |
| $S_{\text{goal}}$ | $\dfrac{1}{G}\sum_g\!\left[0.6\cdot\min\!\left(\dfrac{\text{non-goal spend}}{\text{remaining}_g},1\right)+0.4\cdot\sigma\!\left(\dfrac{d_{\text{now}}}{d_{\text{counterfactual}}}-1\right)\right]$ | Spending that widens the gap to a savings goal forces users to confront sunk cost — the time and money already invested. The velocity component captures the rising daily savings burden. |
| $S_{\text{sub}}$ | $\min\!\left(\dfrac{N_{\text{cancelled within 14d of billing}}}{N_{\text{total subs}}},\;1\right)$ | Rapid cancellation after a billing event is the strongest revealed-preference regret signal — it requires an active corrective action, meaning the user consciously reversed a decision. |
| $S_{\text{night}}$ | $\dfrac{N_{\text{late-night non-essential}}}{N_{\text{total recent}}}$ | Executive function degrades between 11 PM – 4 AM. Purchases made in low-willpower hours on non-essential categories are disproportionately regretted the following morning. |

---

### Resilience Score

$$\text{Resilience} = \sigma\!\left(2.5\,R_{\text{recovery}} + 3.0\,R_{\text{goal}} + 1.5\,R_{\text{structure}} + 1.0\,R_{\text{entropy}} + 2.0\,R_{\text{adherence}} - 4.0\right)$$

| Signal | Formula | Why It Indicates Resilience |
|---|---|---|
| $R_{\text{recovery}}$ | $\dfrac{1}{\|\mathcal{S}\|}\displaystyle\sum_{s\in\mathcal{S}} e^{-0.05\,d_s}$ | Fast balance recovery after a financial shock reveals active management — the user has reserves or immediately adjusts spending. Exponential decay ensures 1–3 day recovery scores far higher than 20+ days. |
| $R_{\text{goal}}$ | $0.6\cdot e^{-\text{CV}} + 0.4\cdot\text{participation rate}$ | A user who contributes to goals consistently — even during hard months — demonstrates self-regulatory persistence. CV captures evenness; participation captures commitment. |
| $R_{\text{structure}}$ | $\exp\!\left(-\dfrac{(r-0.6)^2}{0.08}\right),\quad r=\dfrac{\sum\text{amt}_{\text{fixed}}}{\sum\text{amt}_{\text{all}}}$ | Both too little structure (chaotic spending) and too much (no flexibility buffer) are financial risks. The sweet spot at 60% fixed signals automated essentials with maintained adaptability. |
| $R_{\text{entropy}}$ | $\dfrac{H(\mathbf{p})}{\ln K},\quad H(\mathbf{p})=-\displaystyle\sum_i p_i\ln p_i$ | Spending concentrated in one category signals dependency and vulnerability. A diversified profile reflects balanced life needs rather than compulsive over-indexing. |
| $R_{\text{adherence}}$ | $\dfrac{1}{K}\displaystyle\sum_i e^{-\max(0,\,\delta_i)},\quad\delta_i=\dfrac{\text{spent}_i-\text{budget}_i}{\text{budget}_i}$ | Where goal consistency measures financial offense, budget adherence measures defense. Following through on self-imposed limits is a direct proxy for financial willpower. |

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
