"""API Blueprints 註冊"""

from flask import Flask


def register_blueprints(app: Flask):
    """註冊所有 API Blueprints"""
    from api.auth import auth_bp
    from api.accounts import accounts_bp
    from api.export import export_bp
    from api.categories import categories_bp
    from api.budget import budget_bp
    from api.settings import settings_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(accounts_bp, url_prefix="/api/accounts")
    app.register_blueprint(export_bp, url_prefix="/api/export")
    app.register_blueprint(categories_bp, url_prefix="/api/categories")
    app.register_blueprint(budget_bp, url_prefix="/api/budget")
    app.register_blueprint(settings_bp, url_prefix="/api/settings")
