"""Categories Blueprint — 類別管理 API"""

from flask import Blueprint, request, jsonify, g

from services.category_service import category_service
from middleware.auth import require_auth

categories_bp = Blueprint("categories", __name__)


@categories_bp.route("", methods=["GET"])
@require_auth
def get_categories():
    """查詢所有類別"""
    user_doc_id = g.user["firestore_doc_id"]
    categories = category_service.get_categories(user_doc_id)
    return jsonify({"categories": categories}), 200


@categories_bp.route("", methods=["POST"])
@require_auth
def create_category():
    """新增類別"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "請提供 JSON 資料", "code": "INVALID_BODY"}), 400

    user_doc_id = g.user["firestore_doc_id"]
    result = category_service.create_category(
        user_doc_id,
        name=data.get("name", ""),
        category_id=data.get("id"),
    )
    return jsonify(result), 201


@categories_bp.route("/<int:category_id>", methods=["PUT"])
@require_auth
def update_category(category_id):
    """編輯類別"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "請提供 JSON 資料", "code": "INVALID_BODY"}), 400

    user_doc_id = g.user["firestore_doc_id"]
    result = category_service.update_category(user_doc_id, category_id, data.get("name", ""))
    return jsonify(result), 200


@categories_bp.route("/<int:category_id>", methods=["DELETE"])
@require_auth
def delete_category(category_id):
    """刪除類別"""
    user_doc_id = g.user["firestore_doc_id"]
    category_service.delete_category(user_doc_id, category_id)
    return jsonify({"message": "刪除成功"}), 200
