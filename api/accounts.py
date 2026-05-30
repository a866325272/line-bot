"""Accounts Blueprint — 記帳 CRUD API"""

from flask import Blueprint, request, jsonify, g

from services.account_service import account_service
from middleware.auth import require_auth

accounts_bp = Blueprint("accounts", __name__)


def _get_user_context():
    """取得當前使用者的 doc_id 和 collection"""
    return g.user["firestore_doc_id"], g.user.get("firestore_collection", "Linebot_UserID")


@accounts_bp.route("", methods=["GET"])
@require_auth
def get_accounts():
    """查詢記帳明細（支援月份或自訂日期區間）"""
    month = request.args.get("month")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    user_doc_id, collection = _get_user_context()

    if start_date and end_date:
        accounts = account_service.get_range_accounts(user_doc_id, start_date, end_date, collection)
        return jsonify({"start_date": start_date, "end_date": end_date, "accounts": accounts}), 200
    else:
        if not month:
            month = account_service._get_current_month()
        accounts = account_service.get_monthly_accounts(user_doc_id, month, collection)
        return jsonify({"month": month, "accounts": accounts}), 200


@accounts_bp.route("/summary", methods=["GET"])
@require_auth
def get_summary():
    """月帳統計資料（支援自訂日期區間）"""
    month = request.args.get("month")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    user_doc_id, collection = _get_user_context()

    if start_date and end_date:
        summary = account_service.get_range_summary(user_doc_id, start_date, end_date, collection)
    else:
        if not month:
            month = account_service._get_current_month()
        summary = account_service.get_monthly_summary(user_doc_id, month, collection)

    return jsonify(summary), 200


@accounts_bp.route("/trend", methods=["GET"])
@require_auth
def get_trend():
    """趨勢資料（按月）"""
    start_month = request.args.get("start_month")
    end_month = request.args.get("end_month")

    if not start_month or not end_month:
        return jsonify({"error": "請提供 start_month 和 end_month", "code": "PARAMS_REQUIRED"}), 400

    user_doc_id, collection = _get_user_context()
    trend = account_service.get_trend_data(user_doc_id, start_month, end_month, collection)
    return jsonify(trend), 200


@accounts_bp.route("", methods=["POST"])
@require_auth
def create_account():
    """新增記帳項目"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "請提供 JSON 資料", "code": "INVALID_BODY"}), 400

    user_doc_id, collection = _get_user_context()
    result = account_service.create_account(
        user_doc_id=user_doc_id,
        name=data.get("name", ""),
        amount=data.get("amount"),
        type_id=data.get("type"),
        date=data.get("date"),
        collection=collection,
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

    user_doc_id, collection = _get_user_context()
    result = account_service.update_account(user_doc_id, month, index, data, collection)
    return jsonify(result), 200


@accounts_bp.route("/<int:index>", methods=["DELETE"])
@require_auth
def delete_account(index):
    """刪除單筆記錄"""
    month = request.args.get("month")
    if not month:
        return jsonify({"error": "請提供 month 參數", "code": "MONTH_REQUIRED"}), 400

    user_doc_id, collection = _get_user_context()
    account_service.delete_account(user_doc_id, month, index, collection)
    return jsonify({"message": "刪除成功"}), 200
