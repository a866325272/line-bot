"""匯出業務邏輯 — 匯出明細到 Google Spreadsheet"""

import gss
from services.account_service import account_service
from exceptions import ValidationError, NotFoundError


class ExportService:
    """匯出服務"""

    def export_to_spreadsheet(self, user_doc_id: str, month: str, spreadsheet_id: str) -> str:
        """
        匯出月份明細到 Google Spreadsheet
        重用現有 gss.py 邏輯，產生含 SUMIF、佔比、MoM 公式的統計表

        Returns:
            str: Spreadsheet worksheet URL
        """
        if not spreadsheet_id:
            raise ValidationError("未設定 Spreadsheet ID", "SPREADSHEET_ID_MISSING")

        if not month or len(month) != 7:  # YYYY_MM
            raise ValidationError("月份格式錯誤，請使用 YYYY_MM", "MONTH_INVALID")

        # 取得月份記帳資料（使用原始格式）
        from google.cloud import firestore as firestore_client
        db = firestore_client.Client()
        doc_ref = db.collection("Linebot_UserID").document(user_doc_id)
        doc = doc_ref.get()

        if not doc.exists:
            raise NotFoundError("找不到記帳資料", "ACCOUNTS_NOT_FOUND")

        data = doc.to_dict()
        field_name = f"Accounts_{month}"
        accounts = data.get(field_name, [])

        if not accounts:
            raise NotFoundError("本月沒有記帳記錄", "NO_RECORDS",
                                details={"month": month})

        # 組裝 worksheet 名稱：YYYY_MM
        year = month[:4]
        month_num = month[5:]
        worksheet_name = f"{year}_{month_num}"

        # 計算上個月的 worksheet 名稱（用於 MoM 公式）
        m = int(month_num)
        y = int(year)
        if m == 1:
            old_table = f"{y - 1}_12"
        elif m < 10:
            old_table = f"{y}_0{m - 1}"
        else:
            old_table = f"{y}_{m - 1}"

        # 刪除舊的 worksheet（如果存在）
        gss.delete_worksheet_if_exist(spreadsheet_id, worksheet_name)

        # 建立新 worksheet
        gss.create_worksheet(spreadsheet_id, worksheet_name)

        # 寫入明細資料
        headers = ["Type", "Ammount", "Date", "Name"]
        values = []
        for item in accounts:
            row = [item.get(key, "") for key in headers]
            values.append(row)

        gss.append_data(spreadsheet_id, worksheet_name, [headers])
        gss.append_data(spreadsheet_id, worksheet_name, values)

        # 寫入統計表（含公式）
        update_table = [
            ["", "Type", "Ammount", "percetage", "MoM"],
            ["1", "飲食", '=SUMIF($A$2:$A,"=1",$B$2:$B)', "=G2/$G$13", f'=G2-{old_table}!G2'],
            ["2", "生活", '=SUMIF($A$2:$A,"=2",$B$2:$B)', "=G3/$G$13", f'=G3-{old_table}!G3'],
            ["3", "居住", '=SUMIF($A$2:$A,"=3",$B$2:$B)', "=G4/$G$13", f'=G4-{old_table}!G4'],
            ["4", "交通", '=SUMIF($A$2:$A,"=4",$B$2:$B)', "=G5/$G$13", f'=G5-{old_table}!G5'],
            ["5", "娛樂", '=SUMIF($A$2:$A,"=5",$B$2:$B)', "=G6/$G$13", f'=G6-{old_table}!G6'],
            ["6", "醫療", '=SUMIF($A$2:$A,"=6",$B$2:$B)', "=G7/$G$13", f'=G7-{old_table}!G7'],
            ["7", "其他", '=SUMIF($A$2:$A,"=7",$B$2:$B)', "=G8/$G$13", f'=G8-{old_table}!G8'],
            ["8", "投資", '=SUMIF($A$2:$A,"=8",$B$2:$B)', "=G9/$G$13", f'=G9-{old_table}!G9'],
            ["", "", "", "", ""],
            ["", "", "", "", ""],
            ["11", "收入", '=SUMIF($A$2:$A,"=11",$B$2:$B)', "", f'=G12-{old_table}!G12'],
            ["", "支出", "=SUM(G2:G9)", "", f'=G13-{old_table}!G13'],
            ["", "損益", "=G12-SUM(G2:G9)", "", ""],
        ]

        sheet_url = gss.update_table(spreadsheet_id, worksheet_name, update_table, "E1")

        # 設定百分比格式
        gss.set_format_percent(spreadsheet_id, worksheet_name, 'H2:H9')

        return sheet_url


# Singleton instance
export_service = ExportService()
