# Quantifi User Emotion - Personal Finance Assistant

A full-stack personal finance assistant that combines transaction tracking, budgeting, savings/subscription management, and behavioral insights (`IRS`, `PRS`, `Resilience`) with an AI chatbot for contextual financial guidance.

## Table of Contents

- [Overview](#overview)
- [Core Features](#core-features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [API Overview](#api-overview)
- [Data Model](#data-model)
- [Scoring Model (Core Logic)](#scoring-model)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Security Notes](#security-notes)
- [Known Issues](#known-issues)

## Overview

Quantifi helps users:
- Track income/expense transactions (manual + CSV import)
- Set and monitor category budgets
- Create savings goals with deposits/withdrawals
- Manage recurring subscriptions
- View spending and behavior trends on dashboards
- Receive AI-generated alerts before potentially regrettable spending
- Chat with an assistant that uses user-specific financial context

## Core Features

- **Authentication**
  - Signup and login with JWT-based auth
  - Protected API routes and protected frontend pages

- **Transactions**
  - Manual transaction creation with date/time/category
  - CSV import for bulk transaction ingestion
  - Uncategorized transaction review and categorization
  - Spending distribution and behavior chart data

- **Budgeting**
  - Set per-category monthly budgets
  - Compare budget targets with current spending

- **Savings Goals**
  - Create goals with target/current amount and timeline
  - Deposit into and withdraw from goals
  - Track active and completed goals

- **Subscriptions**
  - Add recurring subscriptions with billing cycles
  - View and deactivate subscriptions
  - Scheduled processing support on backend

- **AI Guidance**
  - Pre-transaction regret alert endpoint
  - Chatbot responses informed by user financial behavior and profile metrics

## Architecture

- **Frontend**: React + TypeScript SPA (Vite), route-protected pages, React Query for server state, Zustand for auth persistence.
- **Backend**: FastAPI app with router/service/repository-style separation and SQLAlchemy async ORM.
- **Database**: PostgreSQL via `asyncpg`.
- **Background Jobs**: APScheduler for periodic subscription-related logic.
- **AI Integration**: OpenAI client for chatbot/advisory behavior.

## Tech Stack

### Backend
- Python
- FastAPI
- SQLAlchemy (async)
- PostgreSQL + `asyncpg`
- Pydantic
- APScheduler
- PyJWT + passlib/bcrypt
- pandas / numpy

### Frontend
- React 18
- TypeScript
- Vite
- React Router
- TanStack Query
- Zustand
- Axios
- Tailwind CSS + Radix UI
- Recharts

## Project Structure

```text
.
|- backend/
|  |- app/
|  |  |- business_logic/     # Domain workflows
|  |  |- core/               # Security, logging, scheduler
|  |  |- dependancies/       # DI providers
|  |  |- repo/               # Data access layer
|  |  |- routers/            # FastAPI route modules
|  |  |- schemas/            # Pydantic request/response + scoring schemas
|  |  |- database.py         # Async engine/session + DB init
|  |  |- main.py             # FastAPI app bootstrap
|  |  |- models.py           # SQLAlchemy models
|  |- requirements.txt
|- frontend/
|  |- src/
|  |  |- api/                # Axios instance
|  |  |- components/         # Shared UI/layout components
|  |  |- features/           # Feature modules (auth, dashboard, etc.)
|  |  |- store/              # Zustand stores
|  |  |- App.tsx             # Routes + providers
|  |  |- main.tsx
|  |- package.json
|- demo.html
|- note.md
```

## API Overview

Base URL (default local): `http://localhost:8000`

### Health
- `GET /` - Service info

### User
- `POST /user/signup` - Register user
- `POST /user/login` - Login and issue bearer token
- `GET /user/balance` - Get current user balance (auth)
- `PUT /user/set_budget` - Set category budgets (auth)
- `GET /user/show_budget` - Get budget values (auth)

### Saving
- `POST /saving/create` - Create saving goal (auth)
- `GET /saving/show_current` - Active goals (auth)
- `GET /saving/show_all` - All goals (auth)
- `POST /saving/deposit/{goal_id}` - Deposit to goal (auth)
- `POST /saving/withdraw/{goal_id}` - Withdraw from goal (auth)
- `DELETE /saving/delete/{goal_id}` - Delete goal (auth)
- `GET /saving/all_amount` - Total saved amount (auth)

### Transaction
- `POST /transaction/manual` - Create transaction (auth)
- `POST /transaction/alert_regret` - Get pre-transaction alert (auth)
- `POST /transaction/import_csv` - Import transactions CSV (auth)
- `GET /transaction/view_uncategorized_transactions` - List uncategorized (auth)
- `PUT /transaction/categorize/{transaction_id}` - Categorize transaction (auth)
- `GET /transaction/view_pie_chart/{cycle}` - Spending distribution (auth)
- `GET /transaction/view_behavior/{cycle}` - Behavior timeline (auth)

### Subscription
- `POST /subscription/create` - Create/reactivate subscription (auth)
- `GET /subscription/me` - List active subscriptions (auth)
- `DELETE /subscription/delete/{subscription_id}` - Deactivate subscription (auth)

### Chatbot / Scoring
- `POST /chatbot/test_irs` - Compute IRS (auth)
- `POST /chatbot/test_prs` - Compute PRS (auth)
- `POST /chatbot/test_resilience` - Compute resilience (auth)
- `POST /chatbot/request` - Chatbot response using user context (auth)

## Data Model

Main SQLAlchemy entities:

- **User**
  - Identity/auth fields, balance, budget caps, profile values (`avg_income`, `avg_outcome`), and stored behavior indicators.
- **Transaction**
  - User-linked financial events with datetime, amount, category, optional subscription/goal linkage.
- **Subscription**
  - Recurring charges with cycle, next billing date, and active status.
- **FinanceGoal**
  - Savings goal metadata, target/current amounts, timeline, and status.

## Scoring Model

Behavior analysis is represented by three score families:

- **IRS** (Impulse-related score)
- **PRS** (Pattern/regularity-related score)
- **Resilience** (Financial resilience score)

These scores are computed in `backend/app/business_logic/financial_preference.py` using schema contracts in:
- `backend/app/schemas/irs.py`
- `backend/app/schemas/prs.py`
- `backend/app/schemas/resilience.py`

### Shared Mechanics

- Most component scores are normalized in `[0, 1]`.
- The code uses numeric safety constants:
  - `EPS = 1e-8` to avoid divide-by-zero.
  - Clamped sigmoid input to `[-20, 20]` for stability.
- Data is fetched by `FinancialPreferenceAnalyzer` from repositories (`UserRepository`, `TransactionRepository`, `SavingRepository`, `SubscriptionRepository`) before score assembly.

### 1) IRS - Immediate Regret Score

IRS estimates regret risk for a single transaction event.

#### IRS Components (`s_*`)

- `s_budget` (Budget breach pressure):  
  `remaining = max(EPS, category_budget - category_spent)`  
  `s_budget = clamp01(txn_amount / remaining)`
- `s_income` (Income shock):  
  `s_income = min(1, (txn_amount / (monthly_income + EPS))^0.7)`
- `s_time` (Temporal vulnerability):
  - `06:00-20:59 => 0.0`
  - `21:00-22:59 => 0.3`
  - `23:00-00:59 => 0.7`
  - `01:00-04:59 => 1.0`
  - `05:00-05:59 => 0.5`
- `s_goal` (Goal conflict): for each active goal, compute urgency and impact:
  - `urgency = 30 / days_left` (with overdue handling)
  - `impact = min(1, (txn_amount / (remaining_needed + EPS)) * urgency)`
  - final `s_goal = max(impact over goals)`
- `s_freq` (Category frequency anomaly):  
  `s_freq = clamp01((recent_count - baseline_weekly_count) / max(baseline_weekly_count + EPS, 1.0))`
- `s_cat` (Category risk lookup): static risk map fallback to moderate default.
- `s_dom` (Day-of-month pressure):  
  `s_dom = max(0, month_remaining_ratio - budget_remaining_ratio)`
- `s_vel` (Spending velocity):  
  `s_vel = min(1, 0.5*(txns_last_2h/5) + 0.5*(amount_last_2h/(daily_budget + EPS)))`

#### IRS Aggregation Pipeline

IRS in schema `ImmediateRegretScore` is not a simple linear sum; it has 3 layers:

1. **Linear weighted score** with V3 weights  
   `w_budget=0.208, w_income=0.189, w_time=0.094, w_goal=0.189, w_freq=0.123, w_cat=0.085, w_dom=0.066, w_vel=0.047`
2. **Convergence penalty** (weather-forecast style): counts active signals above thresholds and adds  
   `penalty = min(0.35, 0.04 * active^1.6)` for `active > 1`
3. **Interaction amplifiers** (pairwise non-linear boosts):
   - `alpha1=0.25`: `s_time * s_vel`
   - `alpha2=0.35`: `s_budget * s_goal`
   - `alpha3=0.20`: `s_freq * s_cat`
   - `alpha4=0.18`: `s_dom * s_budget`
   - `alpha5=0.15`: `s_time * s_income`

Then:
- `raw = min(1.5, (linear + penalty) * amplifier)`
- calibrated sigmoid transform with floor adjustment
- final output rounded to 6 decimals in `[0,1]`.

### 2) PRS - Periodic Regret Score

PRS measures regret pattern over a rolling window (default `lookback_days=14` in analyzer).

#### PRS Components (`s_*`)

- `s_impulse`: average of non-essential frequency ratio and amount ratio.
- `s_budget`: category overshoot transform with bug-fix baseline correction:  
  `s_budget = clamp01(2*sigmoid(3*mean_overshoot) - 1)`  
  (ensures `0` when no overshoot).
- `s_goal`: disruption from non-goal spending against active goals:  
  combines `min(spend/remaining,1)` and velocity impact term.
- `s_sub`: `min(cancelled_subscriptions_14d / (total_subscriptions + EPS), 1)`
- `s_night`: `late_night_non_essential_count / (total_transaction_count + EPS)`
- `s_pressure`: `sigmoid(3*(total_expenses/(total_income + EPS) - 0.7))`, with hard return `1.0` when income `<= 0`.

#### PRS Final Formula

Schema `PeriodicRegretScore` computes:

`PRS = sigmoid(2.0*s_impulse + 2.5*s_budget + 3.0*s_goal + 1.5*s_sub + 1.0*s_night + 2.0*s_pressure - beta)`

where `beta = 3.0` (calibrated after component-floor bug fixes).

### 3) Resilience Score

Resilience estimates medium-term financial robustness (default window `months=4`).

#### Resilience Components (`r_*`)

- `r_recovery` (Balance recovery after dips):
  - simulate running balance from signed transactions
  - detect dip/recovery intervals under threshold `income * shock_pct` (`shock_pct=0.15`)
  - score via average `exp(-0.05 * recovery_days)`
  - fallback rules:
    - no dips and no active unresolved dip -> `0.85`
    - unresolved dip at window end -> `0.30`
    - no transactions -> `0.5`
- `r_goal`:  
  `0.6*exp(-CV(goal_contributions)) + 0.4*participation_rate`
- `r_structure`: Gaussian preference around essential spend ratio `0.6`:  
  `exp(-(r - 0.6)^2 / 0.08)`
- `r_entropy`: normalized Shannon entropy with edge-case fixes:
  - no category -> `0.5`
  - single effective category -> `0.25`
  - otherwise `clamp01(H / ln(k_eff))`
- `r_adherence`: budget adherence from overshoots:  
  `mean(exp(-max(0, overshoot_i)))`; returns `0.0` if no budget data.
- `r_saving`: savings-rate quality and stability:
  - monthly rates `=(income-expense)/(income+EPS)` clamped to `>= -1`
  - `avg_rate` computed only on months with income `> 0`
  - `r_saving = 0.5*sigmoid(5*avg_rate) + 0.5*exp(-2*std_rate)`
- `r_income`: income stability as  
  `exp(-1.5 * CV_income)` with fallback `0.3` when total income is zero.

#### Resilience Final Formula

Schema `ResilienceScore` computes:

`Resilience = sigmoid(1.75*r_recovery + 2.10*r_goal + 1.05*r_structure + 0.70*r_entropy + 1.40*r_adherence + 1.75*r_saving + 1.05*r_income - delta)`

where `delta = 5.5`.

### Runtime Data Windows and Inputs

- IRS: transaction-level, plus recent 2-hour/7-day/90-day and month-to-date context.
- PRS: default 14-day lookback.
- Resilience: default 4 months for trend and consistency signals.
- Category groups used by analyzer:
  - Non-essential: `shopping`, `entertainment`, `other`
  - Essential: `food and drink`, `moving`, `investment`

### Where Scores Are Used

- IRS: pre-transaction regret alert logic and chatbot context.
- PRS and Resilience: periodic behavioral profile used by advisory/chatbot flows and dashboard behavior endpoints.

## Getting Started

### 1) Prerequisites

- Python 3.11+ (3.13 also used in this repo)
- Node.js 18+
- PostgreSQL 14+

### 2) Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The backend initializes tables on startup.

### 3) Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend default Vite URL: `http://localhost:5173`

### 4) Build for Production

```bash
cd frontend
npm run build
npm run preview
```

## Configuration

Current implementation includes defaults in source code. Recommended env variables:

- `DATABASE_URL`  
  Example format: `postgresql+asyncpg://USER:PASSWORD@HOST:5432/DB_NAME`
- `JWT_SECRET_KEY`
- `JWT_ALGORITHM` (default `HS256`)
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` (default `30`)
- `OPENAI_API_KEY`
- `FRONTEND_API_BASE_URL`
- `CORS_ALLOWED_ORIGINS`

Note: backend currently has in-code defaults for some sensitive values; move them to environment variables before production use.

## Security Notes

- Do not commit secrets or API keys.
- Rotate any previously exposed keys immediately.
- Replace wildcard CORS with explicit origin allowlist in production.
- Keep `allow_credentials` aligned with strict CORS origins.
- Prefer `.env` + secret manager integration for deployment.

## Known Issues

- `backend/requirements.txt` has duplicate/ambiguous entries (`apscheduler` repeated, both `jwt` and `pyjwt`, and `logging` listed though it is stdlib).
- Some backend calls appear inconsistent with `process_transaction(...)` parameter requirements.
- Frontend API base URL/proxy configuration is partially duplicated (direct backend URL vs proxy strategy).
- Naming/typing consistency can be improved (`dependancies` directory name, typoed function names in security module).

---

If this README will be used for deployment/onboarding, the next recommended step is adding:
- a `.env.example` for backend/frontend
- database migration workflow (Alembic)
- API schema docs section with example request/response payloads
