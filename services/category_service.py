"""類別管理業務邏輯"""

from google.cloud import firestore as firestore_client

from exceptions import ValidationError, NotFoundError, ConflictError


db = firestore_client.Client()

ACCOUNTS_COLLECTION = "Linebot_UserID"

DEFAULT_CATEGORIES = [
    {"id": 1, "name": "飲食", "is_default": True},
    {"id": 2, "name": "生活", "is_default": True},
    {"id": 3, "name": "居住", "is_default": True},
    {"id": 4, "name": "交通", "is_default": True},
    {"id": 5, "name": "娛樂", "is_default": True},
    {"id": 6, "name": "醫療", "is_default": True},
    {"id": 7, "name": "其他", "is_default": True},
    {"id": 8, "name": "投資", "is_default": True},
    {"id": 11, "name": "收入", "is_default": True},
]


class CategoryService:
    """類別服務"""

    def get_categories(self, user_doc_id: str) -> list:
        """查詢使用者所有類別"""
        doc_ref = db.collection(ACCOUNTS_COLLECTION).document(user_doc_id)
        doc = doc_ref.get()

        if not doc.exists:
            return DEFAULT_CATEGORIES

        data = doc.to_dict()
        categories = data.get("Categories", DEFAULT_CATEGORIES)
        return categories

    def create_category(self, user_doc_id: str, name: str, category_id: int) -> dict:
        """新增自訂類別"""
        if not name or not name.strip():
            raise ValidationError("類別名稱不可為空", "CATEGORY_NAME_REQUIRED")
        if len(name.strip()) > 20:
            raise ValidationError("類別名稱不可超過 20 字元", "CATEGORY_NAME_TOO_LONG")
        if category_id is None:
            raise ValidationError("類別代號不可為空", "CATEGORY_ID_REQUIRED")

        categories = self.get_categories(user_doc_id)

        # 檢查 ID 是否重複
        if any(c["id"] == category_id for c in categories):
            raise ConflictError("類別代號已存在", "CATEGORY_ID_EXISTS",
                                details={"id": category_id})

        # 檢查名稱是否重複
        if any(c["name"] == name.strip() for c in categories):
            raise ConflictError("類別名稱已存在", "CATEGORY_NAME_EXISTS",
                                details={"name": name})

        new_category = {
            "id": int(category_id),
            "name": name.strip(),
            "is_default": False,
        }

        categories.append(new_category)

        doc_ref = db.collection(ACCOUNTS_COLLECTION).document(user_doc_id)
        doc_ref.update({"Categories": categories})

        return new_category

    def update_category(self, user_doc_id: str, category_id: int, name: str) -> dict:
        """更新類別名稱"""
        if not name or not name.strip():
            raise ValidationError("類別名稱不可為空", "CATEGORY_NAME_REQUIRED")

        categories = self.get_categories(user_doc_id)

        # 找到目標類別
        target = None
        for cat in categories:
            if cat["id"] == category_id:
                target = cat
                break

        if not target:
            raise NotFoundError("類別不存在", "CATEGORY_NOT_FOUND")

        # 檢查名稱是否與其他類別重複
        if any(c["name"] == name.strip() and c["id"] != category_id for c in categories):
            raise ConflictError("類別名稱已存在", "CATEGORY_NAME_EXISTS")

        target["name"] = name.strip()

        doc_ref = db.collection(ACCOUNTS_COLLECTION).document(user_doc_id)
        doc_ref.update({"Categories": categories})

        return target

    def delete_category(self, user_doc_id: str, category_id: int):
        """刪除類別（預設類別不可刪除）"""
        categories = self.get_categories(user_doc_id)

        target = None
        for cat in categories:
            if cat["id"] == category_id:
                target = cat
                break

        if not target:
            raise NotFoundError("類別不存在", "CATEGORY_NOT_FOUND")

        if target.get("is_default", False):
            raise ValidationError("預設類別不可刪除", "CANNOT_DELETE_DEFAULT")

        # 檢查是否有記錄使用此類別（簡化：只檢查當月）
        # 完整檢查需要掃描所有月份，這裡先允許刪除並提示
        categories = [c for c in categories if c["id"] != category_id]

        doc_ref = db.collection(ACCOUNTS_COLLECTION).document(user_doc_id)
        doc_ref.update({"Categories": categories})


# Singleton instance
category_service = CategoryService()
