
*As a young team of developers, we candidly acknowledge that we are still refining our skills in building enterprise-grade, "flawless" consumer products. You might find certain UI/UX edges unpolished or some non-core features simplified. However, our primary mission was never to build just another flashy budgeting app. Our absolute focus is the Core Logic. We invested 80% of our energy into the **Financial Behavioral Engine**. We welcome any feedback on our architecture and logic from senior experts.*

# Quantifi User Emotion - Personal Finance Assistant

A full-stack personal finance assistant that combines transaction tracking, budgeting, savings/subscription management, and behavioral insights (`IRS`, `PRS`, `Resilience`) with an AI chatbot for contextual financial guidance.

## Table of Contents

- [Overview](#overview)
- [Core Features](#core-features)
- [Scoring Model (Core Logic)](#scoring-model)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [API Overview](#api-overview)
- [Data Model](#data-model)
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

## Scoring Model

Behavior analysis is represented by three score families:

- **IRS** (Immediate Regret Score)
- **PRS** (Periodic Regret Score)
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

## Getting Started

### 1) Prerequisites

- Python 3.11+ (3.13 also used in this repo)
- Node.js 18+
- PostgreSQL 14+
- Docker 

### 2) Database Setup

```bash
docker-compose up -d
``` 

### 3) Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The backend initializes tables on startup.

### 4) Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend default Vite URL: `http://localhost:5173`

## Configuration

Current implementation includes defaults in source code. Recommended env variables:

- `DATABASE_URL`  
  Example format: `postgresql+asyncpg://USER:PASSWORD@HOST:5432/DB_NAME`
- `JWT_SECRET_KEY`
- `JWT_ALGORITHM` (default `HS256`)
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` (default `30`)
- `OPENAI_API_KEY`

