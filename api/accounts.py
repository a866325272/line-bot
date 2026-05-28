"""Accounts Blueprint — 記帳 CRUD API"""

from flask import Blueprint, request, jsonify, g

from services.account_service import account_service
from middleware.auth import require_auth

accounts_bp = Blueprint("accounts", __name__)


@accounts_bp.route("", methods=["GET"])
@require_auth
def get_accounts():
    """查詢月份記帳明細"""
    month = request.args.get("month")
    if not month:
        # 預設當月
        month = account_service._get_current_month()

    user_doc_id = g.user["firestore_doc_id"]
    accounts = account_service.get_monthly_accounts(user_doc_id, month)
    return jsonify({"month": month, "accounts": accounts}), 200


@accounts_bp.route("/summary", methods=["GET"])
@require_auth
def get_summary():
    """月帳統計資料"""
    month = request.args.get("month")
    if not month:
        month = account_service._get_current_month()

    user_doc_id = g.user["firestore_doc_id"]
    summary = account_service.get_monthly_summary(user_doc_id, month)
    return jsonify(summary), 200


@accounts_bp.route("", methods=["POST"])
@require_auth
def create_account():
    """新增記帳項目"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "請提供 JSON 資料", "code": "INVALID_BODY"}), 400

    user_doc_id = g.user["firestore_doc_id"]
    result = account_service.create_account(
        user_doc_id=user_doc_id,
        name=data.get("name", ""),
        amount=data.get("amount"),
        type_id=data.get("type"),
        date=data.get("date"),
    )
    return jsonify(result), 201


@accounts_bp.route("/<int:index>", methods=["PUT"])
@require_auth
def update_account(index):
    """編輯單筆記錄"""
    month = request.args.get("month")
    if not month:
        return jsonify({"error": "請提供 month 參數", "code": "MONTH_REQUIRED"}), 400

    data = request.get_json()
    if not data:
        return jsonify({"error": "請提供 JSON 資料", "code": "INVALID_BODY"}), 400

    user_doc_id = g.user["firestore_doc_id"]
    result = account_service.update_account(user_doc_id, month, index, data)
    return jsonify(result), 200


@accounts_bp.route("/<int:index>", methods=["DELETE"])
@require_auth
def delete_account(index):
    """刪除單筆記錄"""
    month = request.args.get("month")
    if not month:
        return jsonify({"error": "請提供 month 參數", "code": "MONTH_REQUIRED"}), 400

    user_doc_id = g.user["firestore_doc_id"]
    account_service.delete_account(user_doc_id, month, index)
    return jsonify({"message": "刪除成功"}), 200
