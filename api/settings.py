"""Settings Blueprint — 個人設定 API"""

from datetime import datetime, timezone

from flask import Blueprint, request, jsonify, g
from google.cloud import firestore as firestore_client

from middleware.auth import require_auth
from exceptions import ValidationError

settings_bp = Blueprint("settings", __name__)

db = firestore_client.Client()
USERS_COLLECTION = "Linebot_Users"


@settings_bp.route("", methods=["GET"])
@require_auth
def get_settings():
    """取得個人設定"""
    user_id = g.user["id"]
    doc = db.collection(USERS_COLLECTION).document(user_id).get()

    if not doc.exists:
        return jsonify({}), 200

    data = doc.to_dict()
    return jsonify({
        "spreadsheet_id": data.get("spreadsheet_id", ""),
        "firestore_doc_id": data.get("firestore_doc_id", ""),
    }), 200


@settings_bp.route("", methods=["PUT"])
@require_auth
def update_settings():
    """更新個人設定"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "請提供 JSON 資料", "code": "INVALID_BODY"}), 400

    user_id = g.user["id"]
    update_data = {"updated_at": datetime.now(timezone.utc)}

    # 更新 spreadsheet_id
    if "spreadsheet_id" in data:
        spreadsheet_id = data["spreadsheet_id"].strip()
        if len(spreadsheet_id) > 100:
            raise ValidationError("Spreadsheet ID 格式錯誤", "INVALID_SPREADSHEET_ID")
        update_data["spreadsheet_id"] = spreadsheet_id

    db.collection(USERS_COLLECTION).document(user_id).update(update_data)

    return jsonify({"message": "設定已更新"}), 200
