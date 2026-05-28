"""預算管理業務邏輯"""

from google.cloud import firestore as firestore_client

from exceptions import ValidationError
from services.account_service import account_service


db = firestore_client.Client()

ACCOUNTS_COLLECTION = "Linebot_UserID"


class BudgetService:
    """預算服務"""

    def get_budgets(self, user_doc_id: str) -> dict:
        """查詢所有類別預算設定"""
        doc_ref = db.collection(ACCOUNTS_COLLECTION).document(user_doc_id)
        doc = doc_ref.get()

        if not doc.exists:
            return {}

        data = doc.to_dict()
        return data.get("Budgets", {})

    def set_budget(self, user_doc_id: str, category_id: int, amount: float) -> dict:
        """設定/更新類別月預算"""
        if amount is None:
            raise ValidationError("預算金額不可為空", "BUDGET_AMOUNT_REQUIRED")
        if float(amount) < 0:
            raise ValidationError("預算金額不可為負數", "BUDGET_AMOUNT_NEGATIVE")

        doc_ref = db.collection(ACCOUNTS_COLLECTION).document(user_doc_id)
        doc = doc_ref.get()

        budgets = {}
        if doc.exists:
            budgets = doc.to_dict().get("Budgets", {})

        budgets[str(category_id)] = float(amount)
        doc_ref.update({"Budgets": budgets})

        return {"category_id": category_id, "amount": float(amount)}

    def get_budget_status(self, user_doc_id: str, month: str) -> list:
        """計算各類別預算使用狀況"""
        budgets = self.get_budgets(user_doc_id)
        summary = account_service.get_monthly_summary(user_doc_id, month)

        status = []
        for cat in summary.get("categories", []):
            type_id = cat["type"]
            spent = cat["total"]
            budget = budgets.get(str(type_id), 0)

            if budget > 0:
                percentage = round((spent / budget) * 100, 1)
                over = spent > budget
            else:
                percentage = 0
                over = False

            status.append({
                "category_id": type_id,
                "spent": spent,
                "budget": budget,
                "percentage": percentage,
                "over": over,
            })

        return status


# Singleton instance
budget_service = BudgetService()
