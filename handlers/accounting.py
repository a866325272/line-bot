"""記帳相關: 記帳、月帳統計、月帳明細"""

from datetime import datetime, timezone, timedelta

from matplotlib import pyplot as plt

from config import ACCESS_TOKEN, logger
import firestore
import gcs
import gss
import lma


def accounting(text: str, client: str, ID: str, tk: str):
    """記帳流程（單一 step field 驅動：name → amount → type）"""
    doc_key = 'Linebot_' + client + 'ID'
    step = firestore.get_firestore_field(doc_key, ID, 'accounting_step')

    if step == 'name':
        firestore.update_firestore_field(doc_key, ID, 'accounting_tmp_name', text)
        firestore.update_firestore_field(doc_key, ID, 'accounting_step', 'amount')
        lma.reply_message("請輸入金額", tk, ACCESS_TOKEN)

    elif step == 'amount':
        try:
            amount = float(text)
        except ValueError:
            lma.reply_message("格式錯誤，請輸入金額數字", tk, ACCESS_TOKEN)
            return
        firestore.update_firestore_field(doc_key, ID, 'accounting_tmp_amount', amount)
        firestore.update_firestore_field(doc_key, ID, 'accounting_step', 'type')
        lma.reply_message(_category_prompt(doc_key, ID), tk, ACCESS_TOKEN)

    elif step == 'type':
        valid_ids = _get_valid_category_ids(doc_key, ID)
        try:
            typ = int(text)
            if typ not in valid_ids:
                raise ValueError
        except ValueError:
            lma.reply_message("格式錯誤，" + _category_prompt(doc_key, ID), tk, ACCESS_TOKEN)
            return
        name = firestore.get_firestore_field(doc_key, ID, 'accounting_tmp_name')
        amount = firestore.get_firestore_field(doc_key, ID, 'accounting_tmp_amount')
        date = datetime.now(timezone(timedelta(hours=+8))).strftime("%Y_%m_%d")
        firestore.append_firestore_array_field(
            doc_key, ID, 'Accounts_' + date[:7],
            [{"Name": name, "Ammount": amount, "Type": typ, "Date": date}]
        )
        # 清除狀態
        firestore.delete_firestore_field(doc_key, ID, 'accounting_step')
        firestore.delete_firestore_field(doc_key, ID, 'accounting_tmp_name')
        firestore.delete_firestore_field(doc_key, ID, 'accounting_tmp_amount')
        lma.reply_message(f'項目名稱:{name} 金額:{amount} 類別:{typ} 輸入成功', tk, ACCESS_TOKEN)


def _get_categories(doc_key: str, ID: str) -> list:
    """從 Firestore 取得使用者的類別清單（含自訂類別）"""
    from services.category_service import DEFAULT_CATEGORIES
    categories = firestore.get_firestore_field(doc_key, ID, 'Categories')
    if not categories:
        return DEFAULT_CATEGORIES
    return categories


def _get_valid_category_ids(doc_key: str, ID: str) -> list:
    """取得所有合法的類別代號"""
    return [c['id'] for c in _get_categories(doc_key, ID)]


def _category_prompt(doc_key: str, ID: str) -> str:
    """動態產生類別代號提示訊息"""
    categories = _get_categories(doc_key, ID)
    lines = [f"{c['id']}{c['name']}" for c in categories]
    return "請輸入類別代號\n" + " ".join(lines)


def account_monthly(client: str, ID: str, date: str, tk: str):
    """月帳統計（圓餅圖）"""
    if len(date) != 6 or int(date[:4]) < 1900 or int(date[:4]) > 2399 or int(date[4:]) < 1 or int(date[4:]) > 12:
        lma.reply_message("日期格式錯誤，請輸入年月\nex.202307", tk, ACCESS_TOKEN)
        raise ValueError("account_monthly:月帳函式日期格式錯誤")

    date_key = date[:4] + "_" + date[4:]
    accounts = firestore.get_firestore_field('Linebot_' + client + 'ID', ID, 'Accounts_' + date_key[:7])
    cost_summation = [0, 0, 0, 0, 0, 0, 0, 0]
    income_summation = 0
    for account in accounts:
        for i in range(8):
            if account['Type'] == i + 1:
                cost_summation[i] += account['Ammount']
        if account['Type'] == 11:
            income_summation += account['Ammount']

    percentages = _pie_chart(["飲食", "生活", "居住", "交通", "娛樂", "醫療", "其他", "投資"], cost_summation, "本月統計")
    gcs.upload_blob("asia.artifacts.watermelon-368305.appspot.com", "./accounts-pie-chart.png", f'accounts-pie-chart/pie-chart{tk}.png')
    gcs.make_blob_public("asia.artifacts.watermelon-368305.appspot.com", f'accounts-pie-chart/pie-chart{tk}.png')
    image_url = f'https://storage.googleapis.com/asia.artifacts.watermelon-368305.appspot.com/accounts-pie-chart/pie-chart{tk}.png'

    labels = ["飲食", "生活", "居住", "交通", "娛樂", "醫療", "其他", "投資"]
    contents = []
    for i, label in enumerate(labels):
        contents.append({
            "type": "box", "layout": "vertical", "spacing": "sm", "alignItems": "center",
            "contents": [{"type": "text", "text": f"{label}:{cost_summation[i]}元({percentages[i]})", "wrap": True, "weight": "bold", "size": "sm"}]
        })

    reply_msg = {"type": "carousel", "contents": [{"type": "bubble", "hero": {"type": "image", "size": "full", "aspectRatio": "20:18", "aspectMode": "cover", "url": image_url}, "body": {"type": "box", "layout": "vertical", "spacing": "sm", "contents": [
        {"type": "box", "layout": "vertical", "spacing": "sm", "alignItems": "center", "contents": [{"type": "text", "text": "支出總計:" + str(sum(cost_summation)) + "元", "wrap": True, "weight": "bold", "size": "lg", "color": "#FF0000"}]},
        *contents,
        {"type": "box", "layout": "vertical", "spacing": "sm", "alignItems": "center", "contents": [{"type": "text", "text": "收入總計:" + str(income_summation) + "元", "wrap": True, "weight": "bold", "size": "lg", "color": "#00FF00"}]},
        {"type": "box", "layout": "vertical", "spacing": "sm", "alignItems": "center", "contents": [{"type": "text", "text": "收支損益:" + str(income_summation - sum(cost_summation)) + "元", "wrap": True, "weight": "bold", "size": "lg"}]},
    ]}}]}
    return reply_msg


def account_detail(text: str, client: str, ID: str, tk: str) -> str:
    """月帳明細匯出到 Google Sheets"""
    try:
        if len(text) != 6:
            raise ValueError
        if int(text[:4]) < 1900 or int(text[:4]) > 2399:
            raise ValueError
        if int(text[4:]) < 1 or int(text[4:]) > 12:
            raise ValueError
    except:
        lma.reply_message("格式錯誤，請輸入年月\nex.202307", tk, ACCESS_TOKEN)
        return ""

    if ID == "C047bb57b021d44a237a8dc1a60ba497d":
        spreadsheet_id = "1yUd_x3r0Jv1dm90p8BZIYQxRkgwm2Rrp6ZAduHG2YDY"
    else:
        spreadsheet_id = "1gDQm8KEvNmO5zlzKoCkCbIZ-7BGJUm9NU7aBKxGkn5k"

    data = firestore.get_firestore_field('Linebot_' + client + 'ID', ID, 'Accounts_' + text[:4] + "_" + text[4:])
    sheet_url = _make_sheet(spreadsheet_id, text, data)
    return "明細已匯出，前往:" + sheet_url


def _make_sheet(spreadsheet_id: str, text: str, data):
    """建立 Google Sheets 工作表"""
    headers = ["Type", "Ammount", "Date", "Name"]
    values = []
    for item in data:
        row = [item[key] for key in headers]
        values.append(row)
    gss.delete_worksheet_if_exist(spreadsheet_id, text[:4] + "_" + text[4:])
    gss.create_worksheet(spreadsheet_id, text[:4] + "_" + text[4:])
    gss.append_data(spreadsheet_id, text[:4] + "_" + text[4:], [headers])
    gss.append_data(spreadsheet_id, text[:4] + "_" + text[4:], values)

    if int(text[4:]) == 1:
        old_table = str(int(text[:4]) - 1) + "_12"
    elif int(text[4:]) in [11, 12]:
        old_table = text[:4] + "_" + str(int(text[4:]) - 1)
    else:
        old_table = text[:4] + "_0" + str(int(text[4:]) - 1)

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
    sheet_url = gss.update_table(spreadsheet_id, text[:4] + "_" + text[4:], update_table, "E1")
    gss.set_format_percent(spreadsheet_id, text[:4] + "_" + text[4:], 'H2:H9')
    return sheet_url


def _pie_chart(index: list, value: list, title: str):
    """生成圓餅圖"""
    non_zero_data = [d for d in value if d != 0]
    non_zero_labels = [l for d, l in zip(value, index) if d != 0]
    res = ['0.0%'] * 8

    fig = plt.figure(figsize=(10, 7))
    patches, labels, percentages = plt.pie(non_zero_data, labels=non_zero_labels, autopct='%1.1f%%', textprops={'fontsize': 24})
    percentage_values = [p.get_text() for p in percentages]
    label_values = [l.get_text() for l in labels]
    for l in zip(label_values, percentage_values):
        res[index.index(l[0])] = l[1]
    plt.rcParams['font.sans-serif'] = 'WenQuanYi Zen Hei'
    plt.title(title, fontsize=24)
    plt.tight_layout(pad=0)
    plt.savefig('accounts-pie-chart.png')
    plt.close(fig)
    return res
