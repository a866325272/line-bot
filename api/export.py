"""Export Blueprint — 明細匯出 API"""

from flask import Blueprint, request, jsonify, g

from services.export_service import export_service
from services.auth_service import auth_service
from middleware.auth import require_auth

export_bp = Blueprint("export", __name__)


@export_bp.route("/spreadsheet", methods=["POST"])
@require_auth
def export_to_spreadsheet():
    """匯出月份明細到 Google Spreadsheet"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "請提供 JSON 資料", "code": "INVALID_BODY"}), 400

    month = data.get("month")
    if not month:
        return jsonify({"error": "請提供 month 參數", "code": "MONTH_REQUIRED"}), 400

    user_doc_id = g.user["firestore_doc_id"]

    # 取得使用者的 spreadsheet_id
    user = auth_service.get_user(g.user["id"])
    spreadsheet_id = user.get("spreadsheet_id", "")

    if not spreadsheet_id:
        return jsonify({
            "error": "尚未設定 Spreadsheet ID，請在個人設定中填入",
            "code": "SPREADSHEET_NOT_CONFIGURED"
        }), 400

    sheet_url = export_service.export_to_spreadsheet(user_doc_id, month, spreadsheet_id)

    return jsonify({
        "message": "匯出成功",
        "sheet_url": sheet_url,
    }), 200
