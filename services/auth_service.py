"""認證業務邏輯"""

import os
import re
import uuid
from datetime import datetime, timezone, timedelta

import bcrypt
import jwt
from google.cloud import firestore as firestore_client

from exceptions import AuthError, ValidationError, ConflictError, NotFoundError


JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", "900"))  # 15 min
JWT_REFRESH_TOKEN_EXPIRES = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES", "604800"))  # 7 days

# Firestore client
db = firestore_client.Client()

# 預設類別
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


class AuthService:
    """認證服務"""

    USERS_COLLECTION = "Linebot_Users"
    ACCOUNTS_COLLECTION = "Linebot_UserID"

    # --- Password utilities ---

    @staticmethod
    def hash_password(password: str) -> str:
        """使用 bcrypt 雜湊密碼 (cost=12)"""
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """驗證密碼（constant-time comparison）"""
        return bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8")
        )

    # --- Token utilities ---

    @staticmethod
    def generate_access_token(user_id: str, username: str, firestore_doc_id: str, firestore_collection: str = "Linebot_UserID") -> str:
        """生成 Access Token (15 min)"""
        payload = {
            "sub": user_id,
            "username": username,
            "firestore_doc_id": firestore_doc_id,
            "firestore_collection": firestore_collection,
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(seconds=JWT_ACCESS_TOKEN_EXPIRES),
        }
        return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    @staticmethod
    def generate_refresh_token(user_id: str) -> str:
        """生成 Refresh Token (7 days)"""
        payload = {
            "sub": user_id,
            "type": "refresh",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(seconds=JWT_REFRESH_TOKEN_EXPIRES),
        }
        return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    # --- Validation ---

    @staticmethod
    def validate_username(username: str) -> str:
        """驗證使用者名稱規則"""
        username = username.strip()
        if len(username) < 3:
            raise ValidationError("使用者名稱至少 3 個字元", "USERNAME_TOO_SHORT")
        if len(username) > 50:
            raise ValidationError("使用者名稱不可超過 50 個字元", "USERNAME_TOO_LONG")
        if " " in username:
            raise ValidationError("使用者名稱不可包含空格", "USERNAME_HAS_SPACE")
        return username

    @staticmethod
    def validate_password(password: str):
        """驗證密碼強度規則"""
        if len(password) < 8:
            raise ValidationError("密碼至少 8 個字元", "PASSWORD_TOO_SHORT")
        if not re.search(r"[A-Z]", password):
            raise ValidationError("密碼需包含至少一個大寫字母", "PASSWORD_NO_UPPER")
        if not re.search(r"[a-z]", password):
            raise ValidationError("密碼需包含至少一個小寫字母", "PASSWORD_NO_LOWER")
        if not re.search(r"\d", password):
            raise ValidationError("密碼需包含至少一個數字", "PASSWORD_NO_DIGIT")

    # --- Business logic ---

    def register(self, username: str, password: str, firestore_doc_id: str = None) -> dict:
        """使用者註冊"""
        # 驗證輸入
        username = self.validate_username(username)
        self.validate_password(password)

        # 檢查 username 是否已存在（case-insensitive）
        users_ref = db.collection(self.USERS_COLLECTION)
        existing = users_ref.where("username_lower", "==", username.lower()).limit(1).get()
        if list(existing):
            raise ConflictError("使用者名稱已存在", "USERNAME_EXISTS")

        # 處理 Firestore document ID
        if firestore_doc_id:
            # 驗證指定的 document 是否存在（支援 UserID 和 GroupID）
            doc_exists = False
            target_collection = None
            for collection in ["Linebot_UserID", "Linebot_GroupID"]:
                doc_ref = db.collection(collection).document(firestore_doc_id)
                if doc_ref.get().exists:
                    doc_exists = True
                    target_collection = collection
                    break
            if not doc_exists:
                raise NotFoundError(
                    "指定的 Firestore Document ID 不存在",
                    "DOC_NOT_FOUND",
                    {"firestore_doc_id": firestore_doc_id}
                )
        else:
            # 建立新的 Firestore document
            firestore_doc_id = str(uuid.uuid4()).replace("-", "")
            target_collection = self.ACCOUNTS_COLLECTION
            doc_ref = db.collection(self.ACCOUNTS_COLLECTION).document(firestore_doc_id)
            doc_ref.set({
                "Categories": DEFAULT_CATEGORIES,
                "Budgets": {},
            })

        # Hash password
        password_hash = self.hash_password(password)

        # 建立 User document
        user_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        user_data = {
            "username": username,
            "username_lower": username.lower(),
            "password_hash": password_hash,
            "firestore_doc_id": firestore_doc_id,
            "firestore_collection": target_collection,
            "spreadsheet_id": "",
            "refresh_token_hash": "",
            "created_at": now,
            "updated_at": now,
        }
        users_ref.document(user_id).set(user_data)

        return {
            "id": user_id,
            "username": username,
            "firestore_doc_id": firestore_doc_id,
        }

    def login(self, username: str, password: str) -> dict:
        """使用者登入"""
        if not username or not password:
            raise AuthError("帳號或密碼錯誤", "AUTH_FAILED")

        # 查詢使用者（case-insensitive）
        users_ref = db.collection(self.USERS_COLLECTION)
        results = list(
            users_ref.where("username_lower", "==", username.strip().lower()).limit(1).get()
        )

        if not results:
            raise AuthError("帳號或密碼錯誤", "AUTH_FAILED")

        user_doc = results[0]
        user_data = user_doc.to_dict()
        user_id = user_doc.id

        # 驗證密碼
        if not self.verify_password(password, user_data["password_hash"]):
            raise AuthError("帳號或密碼錯誤", "AUTH_FAILED")

        # 生成 tokens
        access_token = self.generate_access_token(
            user_id, user_data["username"], user_data["firestore_doc_id"],
            user_data.get("firestore_collection", "Linebot_UserID")
        )
        refresh_token = self.generate_refresh_token(user_id)

        # 儲存 refresh token hash
        refresh_hash = self.hash_password(refresh_token)
        users_ref.document(user_id).update({
            "refresh_token_hash": refresh_hash,
            "updated_at": datetime.now(timezone.utc),
        })

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "id": user_id,
                "username": user_data["username"],
                "firestore_doc_id": user_data["firestore_doc_id"],
            }
        }

    def refresh_token(self, refresh_token: str) -> dict:
        """刷新 Access Token"""
        if not refresh_token:
            raise AuthError("未提供 Refresh Token", "REFRESH_TOKEN_MISSING")

        # 驗證 token
        try:
            payload = jwt.decode(refresh_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        except jwt.ExpiredSignatureError:
            raise AuthError("Refresh Token 已過期，請重新登入", "REFRESH_TOKEN_EXPIRED")
        except jwt.InvalidTokenError:
            raise AuthError("無效的 Refresh Token", "REFRESH_TOKEN_INVALID")

        if payload.get("type") != "refresh":
            raise AuthError("無效的 Token 類型", "WRONG_TOKEN_TYPE")

        user_id = payload.get("sub")

        # 查詢使用者
        users_ref = db.collection(self.USERS_COLLECTION)
        user_doc = users_ref.document(user_id).get()
        if not user_doc.exists:
            raise AuthError("使用者不存在", "USER_NOT_FOUND")

        user_data = user_doc.to_dict()

        # 驗證 refresh token hash
        stored_hash = user_data.get("refresh_token_hash", "")
        if not stored_hash or not self.verify_password(refresh_token, stored_hash):
            raise AuthError("Refresh Token 已撤銷", "REFRESH_TOKEN_REVOKED")

        # 生成新的 access token
        access_token = self.generate_access_token(
            user_id, user_data["username"], user_data["firestore_doc_id"],
            user_data.get("firestore_collection", "Linebot_UserID")
        )

        return {"access_token": access_token}

    def logout(self, user_id: str):
        """登出（撤銷 refresh token）"""
        users_ref = db.collection(self.USERS_COLLECTION)
        users_ref.document(user_id).update({
            "refresh_token_hash": "",
            "updated_at": datetime.now(timezone.utc),
        })

    def get_user(self, user_id: str) -> dict:
        """取得使用者資訊"""
        users_ref = db.collection(self.USERS_COLLECTION)
        user_doc = users_ref.document(user_id).get()
        if not user_doc.exists:
            raise NotFoundError("使用者不存在", "USER_NOT_FOUND")

        user_data = user_doc.to_dict()
        return {
            "id": user_doc.id,
            "username": user_data["username"],
            "firestore_doc_id": user_data["firestore_doc_id"],
            "spreadsheet_id": user_data.get("spreadsheet_id", ""),
        }


# Singleton instance
auth_service = AuthService()
