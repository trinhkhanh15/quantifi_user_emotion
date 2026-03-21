from fastapi import APIRouter, Depends, status, HTTPException
from typing import Annotated
from repo.repositories import SavingRepository, UserRepository, TransactionRepository, SubscriptionRepository
from dependancies.injection import get_user_repo, get_transaction_repo, get_subscription_repo, get_saving_repo
from core.security.token import get_current_user
from schemas import user as sche_user, transaction as sche_transaction, subscription as sche_subscription, saving as sche_saving, irs as sche_irs
from business_logic.financial_preference import FinancialPreferenceAnalyzer

router = APIRouter()

@router.post("/test_irs", status_code=status.HTTP_200_OK)
async def show(request: sche_transaction.CreateTransaction,
         user_repo: UserRepository = Depends(get_user_repo),
         transaction_repo: TransactionRepository = Depends(get_transaction_repo),
         subscription_repo: SubscriptionRepository = Depends(get_subscription_repo),
         saving_repo: SavingRepository = Depends(get_saving_repo),
         current_user: Annotated[sche_user.User, Depends(get_current_user)] = None):
    try:
        user_id = current_user.id
        analyzer = FinancialPreferenceAnalyzer(user_repo, transaction_repo, subscription_repo, saving_repo)
        response = await analyzer.to_irs(user_id, request)
        return response
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
@router.post("/test_prs", status_code=status.HTTP_200_OK)
async def show(user_repo: UserRepository = Depends(get_user_repo),
         transaction_repo: TransactionRepository = Depends(get_transaction_repo),
         subscription_repo: SubscriptionRepository = Depends(get_subscription_repo),
         saving_repo: SavingRepository = Depends(get_saving_repo),
         current_user: Annotated[sche_user.User, Depends(get_current_user)] = None):
    try:
        user_id = current_user.id
        analyzer = FinancialPreferenceAnalyzer(user_repo, transaction_repo, subscription_repo, saving_repo)
        response = await analyzer.to_prs(user_id)
        return response
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    

@router.post("/test_resilience", status_code=status.HTTP_200_OK)
async def show(user_repo: UserRepository = Depends(get_user_repo),
         transaction_repo: TransactionRepository = Depends(get_transaction_repo),
         subscription_repo: SubscriptionRepository = Depends(get_subscription_repo),
         saving_repo: SavingRepository = Depends(get_saving_repo),
         current_user: Annotated[sche_user.User, Depends(get_current_user)] = None):
    try:
        user_id = current_user.id
        analyzer = FinancialPreferenceAnalyzer(user_repo, transaction_repo, subscription_repo, saving_repo)
        response = await analyzer.to_resilience(user_id)
        return response
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))