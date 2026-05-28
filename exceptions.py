"""統一例外類別定義"""


class AppError(Exception):
    """應用程式基礎例外"""

    def __init__(self, message: str, code: str, status_code: int = 400, details: dict = None):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self):
        return {
            "error": self.message,
            "code": self.code,
            "details": self.details
        }


class AuthError(AppError):
    """認證相關錯誤 (401)"""

    def __init__(self, message: str = "認證失敗", code: str = "AUTH_FAILED", details: dict = None):
        super().__init__(message, code, status_code=401, details=details)


class ValidationError(AppError):
    """輸入驗證失敗 (400)"""

    def __init__(self, message: str = "輸入驗證失敗", code: str = "VALIDATION_ERROR", details: dict = None):
        super().__init__(message, code, status_code=400, details=details)


class NotFoundError(AppError):
    """資源不存在 (404)"""

    def __init__(self, message: str = "資源不存在", code: str = "NOT_FOUND", details: dict = None):
        super().__init__(message, code, status_code=404, details=details)


class ConflictError(AppError):
    """資源衝突 (409)"""

    def __init__(self, message: str = "資源衝突", code: str = "CONFLICT", details: dict = None):
        super().__init__(message, code, status_code=409, details=details)
