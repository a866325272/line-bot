"""Budget Blueprint — 預算設定 API"""

from flask import Blueprint, request, jsonify, g

from services.budget_service import budget_service
from services.account_service import account_service
from middleware.auth import require_auth

budget_bp = Blueprint("budget", __name__)


@budget_bp.route("", methods=["GET"])
@require_auth
def get_budgets():
    """查詢所有預算設定"""
    user_doc_id = g.user["firestore_doc_id"]
    budgets = budget_service.get_budgets(user_doc_id)
    return jsonify({"budgets": budgets}), 200


@budget_bp.route("/status", methods=["GET"])
@require_auth
def get_budget_status():
    """查詢預算使用狀況"""
    month = request.args.get("month")
    if not month:
        month = account_service._get_current_month()

    user_doc_id = g.user["firestore_doc_id"]
    status = budget_service.get_budget_status(user_doc_id, month)
    return jsonify({"month": month, "status": status}), 200


@budget_bp.route("/<int:category_id>", methods=["PUT"])
@require_auth
def set_budget(category_id):
    """設定/更新類別預算"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "請提供 JSON 資料", "code": "INVALID_BODY"}), 400

    user_doc_id = g.user["firestore_doc_id"]
    result = budget_service.set_budget(user_doc_id, category_id, data.get("amount"))
    return jsonify(result), 200
