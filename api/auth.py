"""Auth Blueprint — 使用者認證 API"""

import os

from flask import Blueprint, request, jsonify, make_response

from services.auth_service import auth_service
from middleware.auth import require_auth
from flask import g

auth_bp = Blueprint("auth", __name__)

JWT_REFRESH_TOKEN_EXPIRES = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES", "604800"))


@auth_bp.route("/register", methods=["POST"])
def register():
    """使用者註冊"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "請提供 JSON 資料", "code": "INVALID_BODY"}), 400

    username = data.get("username", "")
    password = data.get("password", "")
    firestore_doc_id = data.get("firestore_doc_id")  # 選填

    # 註冊
    user = auth_service.register(username, password, firestore_doc_id)

    # 自動登入
    login_result = auth_service.login(username, password)

    # 設定 refresh token cookie
    response = make_response(jsonify({
        "access_token": login_result["access_token"],
        "user": login_result["user"],
    }))
    response.set_cookie(
        "refresh_token",
        login_result["refresh_token"],
        httponly=True,
        secure=os.getenv("FLASK_ENV") == "production",
        samesite="Strict",
        max_age=JWT_REFRESH_TOKEN_EXPIRES,
        path="/api/auth",
    )
    return response, 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """使用者登入"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "請提供 JSON 資料", "code": "INVALID_BODY"}), 400

    username = data.get("username", "")
    password = data.get("password", "")

    result = auth_service.login(username, password)

    # 設定 refresh token cookie
    response = make_response(jsonify({
        "access_token": result["access_token"],
        "user": result["user"],
    }))
    response.set_cookie(
        "refresh_token",
        result["refresh_token"],
        httponly=True,
        secure=os.getenv("FLASK_ENV") == "production",
        samesite="Strict",
        max_age=JWT_REFRESH_TOKEN_EXPIRES,
        path="/api/auth",
    )
    return response, 200


@auth_bp.route("/refresh", methods=["POST"])
def refresh():
    """刷新 Access Token"""
    refresh_token = request.cookies.get("refresh_token")
    result = auth_service.refresh_token(refresh_token)
    return jsonify(result), 200


@auth_bp.route("/logout", methods=["POST"])
@require_auth
def logout():
    """登出"""
    user_id = g.user["id"]
    auth_service.logout(user_id)

    response = make_response(jsonify({"message": "登出成功"}))
    response.delete_cookie("refresh_token", path="/api/auth")
    return response, 200


@auth_bp.route("/me", methods=["GET"])
@require_auth
def get_me():
    """取得當前使用者資訊"""
    user_id = g.user["id"]
    user = auth_service.get_user(user_id)
    return jsonify(user), 200
