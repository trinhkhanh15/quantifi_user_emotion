# Finance Assistant
An AI application helping users track spending, plan budgets and improve financial habits.

## Problems and Solutions
Many people, ranging from teenagers to adults, struggle to make a saving plan, as they find it hard to track their expenditure and avoid impulsive buying. Other financial tools might help to plan budgets mannually, but users are not motivated to follow these plans.

Therefore, Finance Assistance provides visualised charts of monthly spending, allows users to plan budgets, **and automatically gives personalised advice on financial decision-making.** In that way, users can take into account whether they should buy something or not, reducing chances of impulsive buying.

## Features
Key features:
- 📊 Expense tracking
- 💰 Savings tracking
- 📅 Monthly budget planning
- 🔔 Reminders for overspending
- **✅ Financial decision-making advice**

## Installation

## App Structure
### 1. Backend
This app uses the following data pipeline:
```text
User → Routers → Business Logic → Repositories
```
#### 1.1. Routers
```app\routers``` includes functions for data inputs.
```bash
routers/
├── __pycache__
├── quantifi.py
├── saving.py
├── subscription.py
├── transaction.py
└── user.py
```
#### 1.2. Bussiness Logic
```app\business_logic``` includes CRUD functions and others related.
```bash
business_logic/
├── __pycache__
├── financial_preference.py
├── saving.py
├── subscription.py
├── transaction.py
└── user.py
```
#### 1.3. Repositories
```app\repo``` includes functions for pushing processed data to database.
```bash
repo/
├── __pycache__
└── repositories.py
```

### 2. Frontend
This app uses the following UI data flow:
```text
User → UI Components → Hooks → API Layer → Backend
```
#### 2.1. UI Components
```src\components```includes reusable UI components and layouts.
```bash
components/
├── layout/
│   └── AppLayout.tsx
└── ui/
    ├── button.tsx
    ├── card.tsx
    ├── dialog.tsx
    ├── input.tsx
    ├── label.tsx
    ├── skeleton.tsx
    ├── toast.tsx
    └── toaster.tsx
```
#### 2.2. Hooks
```src\hooks``` contains custom React hooks for shared logic.
```bash
hooks/
└── use-toast.ts
```
#### 2.3. API Layer
```src\api``` handles API configuration and HTTP requests.
```bash
hooks/
└── axios.ts
```
