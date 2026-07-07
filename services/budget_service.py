"""預算管理業務邏輯"""

from google.cloud import firestore as firestore_client

from exceptions import ValidationError
from services.account_service import account_service


db = firestore_client.Client()

ACCOUNTS_COLLECTION = "Linebot_UserID"


class BudgetService:
    """預算服務"""

    def get_budgets(self, user_doc_id: str, collection: str = None) -> dict:
        """查詢所有類別預算設定"""
        col = collection or ACCOUNTS_COLLECTION
        doc_ref = db.collection(col).document(user_doc_id)
        doc = doc_ref.get()

        if not doc.exists:
            return {}

        data = doc.to_dict()
        return data.get("Budgets", {})

    def set_budget(self, user_doc_id: str, category_id: int, amount: float, collection: str = None) -> dict:
        """設定/更新類別月預算"""
        if amount is None:
            raise ValidationError("預算金額不可為空", "BUDGET_AMOUNT_REQUIRED")
        if float(amount) < 0:
            raise ValidationError("預算金額不可為負數", "BUDGET_AMOUNT_NEGATIVE")

        col = collection or ACCOUNTS_COLLECTION
        doc_ref = db.collection(col).document(user_doc_id)
        doc = doc_ref.get()

        budgets = {}
        if doc.exists:
            budgets = doc.to_dict().get("Budgets", {})

        budgets[str(category_id)] = float(amount)
        doc_ref.update({"Budgets": budgets})

        return {"category_id": category_id, "amount": float(amount)}

    def get_budget_status(self, user_doc_id: str, month: str, collection: str = None) -> list:
        """計算各類別預算使用狀況"""
        budgets = self.get_budgets(user_doc_id, collection)
        summary = account_service.get_monthly_summary(user_doc_id, month, collection)

        # 本月各類別花費（可能只涵蓋有交易的類別）
        spent_by_cat = {int(cat["type"]): cat["total"] for cat in summary.get("categories", [])}

        # 涵蓋「有設定預算」與「本月有花費」的所有類別，
        # 避免有預算但本月尚未花費的類別被漏掉
        all_ids = {int(k) for k in budgets.keys()} | set(spent_by_cat.keys())

        status = []
        for type_id in sorted(all_ids):
            spent = spent_by_cat.get(type_id, 0)
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
