"""記帳業務邏輯 — LINE Bot 和 Web UI 共用"""

from datetime import datetime, timezone, timedelta

from google.cloud import firestore as firestore_client

from exceptions import ValidationError, NotFoundError


db = firestore_client.Client()

ACCOUNTS_COLLECTION = "Linebot_UserID"


class AccountService:
    """記帳服務"""

    # --- Validation ---

    @staticmethod
    def validate_account_data(name: str, amount: float, type_id: int, date: str = None):
        """驗證記帳資料"""
        if not name or not name.strip():
            raise ValidationError("項目名稱不可為空", "NAME_REQUIRED")
        if len(name.strip()) > 100:
            raise ValidationError("項目名稱不可超過 100 字元", "NAME_TOO_LONG")
        if amount is None:
            raise ValidationError("金額不可為空", "AMOUNT_REQUIRED")
        try:
            amount = float(amount)
        except (TypeError, ValueError):
            raise ValidationError("金額必須為數字", "AMOUNT_INVALID")
        if amount <= 0:
            raise ValidationError("金額必須為正數", "AMOUNT_POSITIVE",
                                  details={"field": "amount", "value": amount})
        if type_id is None:
            raise ValidationError("類別不可為空", "TYPE_REQUIRED")
        if date:
            # 驗證日期格式 YYYY_MM_DD
            try:
                parts = date.split("_")
                if len(parts) != 3:
                    raise ValueError
                int(parts[0]), int(parts[1]), int(parts[2])
            except (ValueError, AttributeError):
                raise ValidationError("日期格式錯誤，請使用 YYYY_MM_DD", "DATE_INVALID")

    @staticmethod
    def _get_month_from_date(date: str) -> str:
        """從日期 YYYY_MM_DD 取得月份 YYYY_MM"""
        parts = date.split("_")
        return f"{parts[0]}_{parts[1]}"

    @staticmethod
    def _get_today_date() -> str:
        """取得今天日期 YYYY_MM_DD（台灣時區）"""
        tw_tz = timezone(timedelta(hours=8))
        return datetime.now(tw_tz).strftime("%Y_%m_%d")

    @staticmethod
    def _get_current_month() -> str:
        """取得當月 YYYY_MM（台灣時區）"""
        tw_tz = timezone(timedelta(hours=8))
        return datetime.now(tw_tz).strftime("%Y_%m")

    # --- CRUD Operations ---

    def create_account(self, user_doc_id: str, name: str, amount: float,
                       type_id: int, date: str = None) -> dict:
        """新增記帳項目"""
        if not date:
            date = self._get_today_date()

        self.validate_account_data(name, amount, type_id, date)

        month = self._get_month_from_date(date)
        field_name = f"Accounts_{month}"

        account_entry = {
            "Name": name.strip(),
            "Ammount": float(amount),
            "Type": int(type_id),
            "Date": date,
        }

        # 追加到 Firestore 陣列
        doc_ref = db.collection(ACCOUNTS_COLLECTION).document(user_doc_id)
        doc_ref.update({
            field_name: firestore_client.ArrayUnion([account_entry])
        })

        return account_entry

    def get_monthly_accounts(self, user_doc_id: str, month: str) -> list:
        """查詢指定月份所有記帳記錄"""
        if not month:
            month = self._get_current_month()

        field_name = f"Accounts_{month}"
        doc_ref = db.collection(ACCOUNTS_COLLECTION).document(user_doc_id)
        doc = doc_ref.get()

        if not doc.exists:
            return []

        data = doc.to_dict()
        accounts = data.get(field_name, [])

        # 加入 index 方便前端編輯/刪除
        result = []
        for i, account in enumerate(accounts):
            result.append({
                "index": i,
                "name": account.get("Name", ""),
                "amount": account.get("Ammount", 0),
                "type": account.get("Type", 0),
                "date": account.get("Date", ""),
            })
        return result

    def update_account(self, user_doc_id: str, month: str, index: int, data: dict) -> dict:
        """更新指定月份的第 index 筆記錄"""
        field_name = f"Accounts_{month}"
        doc_ref = db.collection(ACCOUNTS_COLLECTION).document(user_doc_id)
        doc = doc_ref.get()

        if not doc.exists:
            raise NotFoundError("找不到記帳資料", "ACCOUNTS_NOT_FOUND")

        doc_data = doc.to_dict()
        accounts = doc_data.get(field_name, [])

        if index < 0 or index >= len(accounts):
            raise NotFoundError("找不到指定的記錄", "RECORD_NOT_FOUND",
                                details={"index": index, "total": len(accounts)})

        # 驗證更新資料
        name = data.get("name", accounts[index].get("Name"))
        amount = data.get("amount", accounts[index].get("Ammount"))
        type_id = data.get("type", accounts[index].get("Type"))
        date = data.get("date", accounts[index].get("Date"))

        self.validate_account_data(name, amount, type_id, date)

        # 更新陣列中的項目
        accounts[index] = {
            "Name": name.strip(),
            "Ammount": float(amount),
            "Type": int(type_id),
            "Date": date,
        }

        doc_ref.update({field_name: accounts})

        return {
            "index": index,
            "name": accounts[index]["Name"],
            "amount": accounts[index]["Ammount"],
            "type": accounts[index]["Type"],
            "date": accounts[index]["Date"],
        }

    def delete_account(self, user_doc_id: str, month: str, index: int):
        """刪除指定月份的第 index 筆記錄"""
        field_name = f"Accounts_{month}"
        doc_ref = db.collection(ACCOUNTS_COLLECTION).document(user_doc_id)
        doc = doc_ref.get()

        if not doc.exists:
            raise NotFoundError("找不到記帳資料", "ACCOUNTS_NOT_FOUND")

        doc_data = doc.to_dict()
        accounts = doc_data.get(field_name, [])

        if index < 0 or index >= len(accounts):
            raise NotFoundError("找不到指定的記錄", "RECORD_NOT_FOUND",
                                details={"index": index, "total": len(accounts)})

        # 移除項目
        accounts.pop(index)
        doc_ref.update({field_name: accounts})

    def get_monthly_summary(self, user_doc_id: str, month: str) -> dict:
        """計算月帳統計"""
        accounts = self.get_monthly_accounts(user_doc_id, month)

        # 類別統計
        category_totals = {}
        income_total = 0
        expense_total = 0

        for account in accounts:
            type_id = account["type"]
            amount = account["amount"]

            if type_id == 11:
                income_total += amount
            else:
                expense_total += amount
                category_totals[type_id] = category_totals.get(type_id, 0) + amount

        # 計算百分比
        categories = []
        for type_id, total in sorted(category_totals.items()):
            percentage = (total / expense_total * 100) if expense_total > 0 else 0
            categories.append({
                "type": type_id,
                "total": total,
                "percentage": round(percentage, 1),
            })

        return {
            "month": month,
            "expense_total": expense_total,
            "income_total": income_total,
            "balance": income_total - expense_total,
            "categories": categories,
            "record_count": len(accounts),
        }


# Singleton instance
account_service = AccountService()
