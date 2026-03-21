from repo.repositories import SavingRepository, UserRepository, TransactionRepository, SubscriptionRepository
from business_logic.financial_preference import FinancialPreferenceAnalyzer
from schemas import transaction as sche_transaction
from google import genai    
from datetime import date

class LLModel:
    def __init__(self,
                 user_id: int,
                 transaction: sche_transaction.CreateTransaction,
                 user_repo: UserRepository,
                 transaction_repo: TransactionRepository,
                 subscription_repo: SubscriptionRepository,
                 saving_repo: SavingRepository):
        self.user_id = user_id
        self.transaction = transaction
        self.user_repo = user_repo
        self.transaction_repo = transaction_repo
        self.subscription_repo = subscription_repo
        self.saving_repo = saving_repo

    data = {}
    async def request(self, context: str):
        analyzer = FinancialPreferenceAnalyzer(self.user_repo, self.transaction_repo, self.subscription_repo, self.saving_repo)
        irs = await analyzer.to_irs(self.user_id, self.transaction)
        prs = await analyzer.to_prs(self.user_id)
        resilience = await analyzer.to_resilience(self.user_id)

        today = date.today()
        monthly_income = await self.transaction_repo.get_monthly_income(self.user_id, date(today.year, today.month, 1), today)
        monthly_budget = await self.user_repo.get_monthly_budget(self.user_id)
        spend_this_month = await self.transaction_repo.get_monthly_spending(self.user_id, date(today.year, today.month, 1), today)
        current_saving = await self.saving_repo.get_by_user_id_and_status(self.user_id, "Processing")

        self.data.update({
            "context": context,
            "irs": irs,
            "prs": prs,
            "resilience": resilience,
            "monthly_income": monthly_income,
            "monthly_budget": monthly_budget,
            "spend_this_month": spend_this_month,
            "current_saving": current_saving
        })

    async def response(self):
        try:
            client = genai.Client(api_key="your-api-key")

            rulebook = f"""
        Your name is Gugugaga - the helpful finance assistant that gives advice based on user's financial data. Give a short, clear response.
        Your character is active, friendly, knowledgeable, and supportive.
        Here are some parameters you need to understand:
        - IRS (Immediate regret score): measures the user's feelings of regret after making a financial decision. (everytime user makes a transaction)
        - PRS (Period regret score): measures the user's feelings of regret after the series of financial decision. (2 weeks)
        - Resilience: evaluates the user's ability to cope with financial setbacks. (1 month)
        IRS and PRS are in the range of 0 to 1, with 0 being no regret and 1 being extreme regret.
        Resilience is also scored from 0 to 1, with 0 being no resilience and 1 being high resilience level.
        Do not use any markdown file format.
        Do not mention any parameters (IRS, PRS, Resilience).
        """

            alert_prompt = f"""
        User is gonna make a financial decision. Here are the user's data:
        - IRS: {self.data.get("irs")}
        - PRS: {self.data.get("prs")}
        - Transaction Amount: {self.transaction.amount}
        - Transaction Category: {self.transaction.category}
        - Resilience: {self.data.get("resilience")}
        - Monthly Income: {self.data.get("monthly_income")}
        - Monthly Budget: {self.data.get("monthly_budget")}
        - Spend This Month: {self.data.get("spend_this_month")}
        If IRS < 0.65, you can said something supportive.
        If IRS >= 0.65, you need to alert the user about their high regret level. Then you should ask user to consider their financial situation more carefully before making a decision.
        Maximum 4 sentences.
        """

            chatbot_prompt = f"""
        User have some future plan, they asking you about their financial situation.
        Here are the user's data:
        - PRS: {self.data.get("prs")}
        - Resilience: {self.data.get("resilience")}
        - Monthly Income: {self.data.get("monthly_income")}
        - Monthly Budget: {self.data.get("monthly_budget")}
        - Spend This Month: {self.data.get("spend_this_month")}
        - Current Saving: {self.data.get("current_saving")}
        They asking: "{self.data.get("context")}". 
        Identifying the user's message purpose, if they give all relevant information, you need to address it directly.
        OUTPUT STRUCTURE:
        * If the information is not clear (uncertain or the long future plan > 6 months), sorry and give the reason.
        1. Greet with energy
        2. Answer the query directly using the user's financial data.
        3. Give exactly ONE actionable tip.
        4. End with an encouraging catchphrase.
        If not, you need to ask clarifying questions.
        """

            if self.transaction.description == "consultation":
                prompt = chatbot_prompt
            else:
                prompt = alert_prompt

            model = client.models.generate_content(
                model="gemini-2.5-flash",
                config={
                    "system_instruction": rulebook
                },
                contents=prompt,
            )

            return model.text
        except Exception as e:
            print(f"Google GenAI Error: {str(e)}")
            import traceback
            traceback.print_exc()
            raise

