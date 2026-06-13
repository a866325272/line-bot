"""LINE Bot Webhook 路由與訊息分派"""

import json
import time

from flask import Blueprint, request
from linebot import WebhookHandler
from datetime import datetime, timezone, timedelta

from config import SECRET, ACCESS_TOKEN, logger, exception_handler
import firestore
import lma

from handlers.weather import current_weather, aqi, forecast, earthquake, earthquake_yt, typhoon, radar_video, satellite_video
from handlers.accounting import accounting, account_monthly, account_detail
from handlers.news import news
from handlers.crypto import get_cryptocurrency_market, cryptocurrency
from handlers.chat import chatmode, single_chat, dalle
from handlers.entertainment import get_beauty, get_meme, get_food, get_luck
from handlers.restaurant import find_nearby_restaurants
from handlers.media import speech_to_text, interpretation

webhook_bp = Blueprint('webhook', __name__)

# --- 指令說明 ---
HELP_MESSAGES = {
    '!help': '指令說明\n扛 或 坦 - 打了你就知道啦~~\n抽 - 抽美女帥哥圖\n午餐,晚餐,肚子餓,吃什麼 - 幫你決定吃什麼\n餐廳<地點> - <地點>附近一公里餐廳排名\n聊， - GPT-4對話\n畫， - DALL-E-3合成圖片\n星座 例如:處女  - 回報運勢\n語音訊息 - 語音翻譯機翻成繁體中文\n!加密貨幣 - 加密貨幣指令說明\n!氣象 - 氣象指令說明\n!新聞 - 新聞指令說明\n!對話模式 - 對話模式指令說明',
    '!加密貨幣': '加密貨幣指令說明\n加密貨幣:列表 - 顯示交易對列表\n加密貨幣:<交易對id> - 顯示價格',
    '!氣象': '氣象指令說明\n地震 - 傳送最近一筆地震資訊\n雷達回波 - 傳送雷達回波圖\n衛星雲圖 - 傳送衛星雲圖\n颱風 - 颱風路徑預測\n發送位置 - 回報天氣資訊和預報',
    '!記帳': '記帳指令說明\n記帳 - 紀錄新項目\n月帳 - 當月統計\n歷史 - 歷史月帳\n明細 - 傳送明細到雲端硬碟',
    '!新聞': '新聞指令說明\n焦點新聞 - 三則焦點新聞\n國際新聞 - 三則國際新聞\n商業新聞 - 三則商業新聞\n科技新聞 - 三則科技新聞\n體育新聞 - 三則體育新聞\n娛樂新聞 - 三則娛樂新聞',
    '!對話模式': '對話模式指令說明\n開始對話模式 - 開始ChatGPT對話模式\n結束對話模式 - 結束ChatGPT對話模式\n清空對話紀錄 - 在對話模式過程中使用此指令，可讓ChatGPT遺忘先前的對話紀錄',
}

# 星座列表
ZODIAC_SIGNS = ("牡羊", "金牛", "雙子", "巨蟹", "獅子", "處女", "天秤", "天蠍", "射手", "魔羯", "水瓶", "雙魚")
FOOD_TRIGGERS = ("午餐", "晚餐", "肚子餓", "吃甚麼", "吃什麼")
NEWS_CATEGORIES = ("焦點新聞", "國際新聞", "商業新聞", "科技新聞", "體育新聞", "娛樂新聞")


@webhook_bp.route("/", methods=['POST'])
def linebot():
    body = request.get_data(as_text=True)
    try:
        json_data = json.loads(body)
        handler = WebhookHandler(SECRET)
        signature = request.headers['X-Line-Signature']
        handler.handle(body, signature)

        # LINE verify event（events 為空）
        if not json_data.get('events'):
            return 'OK'

        tk = json_data['events'][0]['replyToken']
        user_id = json_data['events'][0]['source']['userId']
        client = "User"
        ID = user_id
        try:
            group_id = json_data['events'][0]['source']['groupId']
            client = "Group"
            ID = group_id
        except:
            pass

        msg_type = json_data['events'][0]['message']['type']

        if msg_type == 'location':
            _handle_location(json_data, tk)
        elif msg_type == 'audio':
            _handle_audio(json_data, tk)
        elif msg_type == 'text':
            text = json_data['events'][0]['message']['text']
            logger.info(text)
            _handle_text(text, tk, client, ID)
        elif msg_type in ('sticker', 'video', 'image'):
            logger.info(msg_type)

    except Exception as e:
        exception_handler(e)
    return 'OK'


def _handle_location(json_data, tk):
    address = json_data['events'][0]['message']['address'].replace('台', '臺').replace('区', '區')
    lma.reply_message(f'{current_weather(address)}\n\n{aqi(address)}\n\n{forecast(address)}', tk, ACCESS_TOKEN)


def _handle_audio(json_data, tk):
    message_id = json_data['events'][0]['message']['id']
    reply_msg = interpretation(speech_to_text(message_id), tk)
    lma.reply_multi_message(reply_msg, tk, ACCESS_TOKEN)


def _handle_text(text: str, tk: str, client: str, ID: str):
    """文字訊息分派"""
    doc_key = 'Linebot_' + client + 'ID'

    # 狀態機判斷（對話模式、記帳流程）
    if firestore.get_firestore_field(doc_key, ID, 'IsTalking'):
        chatmode(text, client, ID, tk)
        return

    accounting_step = firestore.get_firestore_field(doc_key, ID, 'accounting_step')
    if accounting_step:
        if accounting_step == 'history':
            firestore.delete_firestore_field(doc_key, ID, 'accounting_step')
            lma.reply_flex_message(text, account_monthly(client, ID, text, tk), tk, ACCESS_TOKEN)
        elif accounting_step == 'report':
            firestore.delete_firestore_field(doc_key, ID, 'accounting_step')
            lma.reply_message(account_detail(text, client, ID, tk), tk, ACCESS_TOKEN)
        else:
            accounting(text, client, ID, tk)
        return

    # 一般指令分派
    # 支援全形驚嘆號
    normalized = text.replace('！', '!')

    # Help 指令
    if normalized in HELP_MESSAGES or normalized.replace('!', '！') in HELP_MESSAGES:
        key = normalized if normalized in HELP_MESSAGES else text
        # 找到匹配的 key
        for k in HELP_MESSAGES:
            if normalized == k or normalized == k.replace('!', '！'):
                lma.reply_message(HELP_MESSAGES[k], tk, ACCESS_TOKEN)
                return

    # 氣象類
    if text in ('雷達', '雷達回波'):
        radar_video(tk)
    elif text in ('衛星雲圖', '雲圖'):
        satellite_video(tk)
    elif text == '颱風':
        typhoon(tk, ID)
    elif text in ('地震資訊', '地震'):
        earthquake(tk)

    # OpenAI 類
    elif text[0:2] in ('畫，', '畫,'):
        lma.reply_image(dalle(text[2:]), tk, ACCESS_TOKEN)
    elif text[0:2] in ('聊，', '聊,'):
        lma.reply_message(single_chat(text[2:]), tk, ACCESS_TOKEN)

    # 娛樂類
    elif text in ('扛', '坦'):
        lma.reply_image(get_meme(), tk, ACCESS_TOKEN)
    elif text == '抽':
        lma.reply_image(get_beauty(), tk, ACCESS_TOKEN)
    elif text in ZODIAC_SIGNS:
        lma.reply_message(get_luck(text), tk, ACCESS_TOKEN)
    elif text in FOOD_TRIGGERS:
        lma.reply_image(get_food(), tk, ACCESS_TOKEN)

    # 餐廳
    elif text[0:2] == '餐廳':
        lma.reply_flex_message(text, find_nearby_restaurants(text[2:]), tk, ACCESS_TOKEN)

    # 加密貨幣
    elif normalized in ('加密貨幣:列表', '加密貨幣：列表'):
        lma.reply_message(get_cryptocurrency_market(), tk, ACCESS_TOKEN)
    elif text[0:5] in ('加密貨幣:', '加密貨幣：'):
        lma.reply_message(cryptocurrency(text[5:]), tk, ACCESS_TOKEN)

    # 對話模式
    elif text[0:6] == '開始對話模式':
        firestore.update_firestore_field('Linebot_' + client + 'ID', ID, 'IsTalking', True)
        firestore.delete_firestore_field('Linebot_' + client + 'ID', ID, 'messages')
        lma.reply_message('對話模式已開始', tk, ACCESS_TOKEN)

    # 新聞
    elif text in NEWS_CATEGORIES:
        lma.reply_flex_message(text, news(text), tk, ACCESS_TOKEN)

    # 記帳
    elif text == "記帳":
        firestore.update_firestore_field('Linebot_' + client + 'ID', ID, 'accounting_step', 'name')
        lma.reply_message('請輸入項目名稱', tk, ACCESS_TOKEN)
    elif text == "月帳":
        reply_msg = account_monthly(client, ID, datetime.now(timezone(timedelta(hours=+8))).strftime("%Y%m"), tk)
        lma.reply_flex_message(text, reply_msg, tk, ACCESS_TOKEN)
    elif text == "歷史":
        firestore.update_firestore_field('Linebot_' + client + 'ID', ID, 'accounting_step', 'history')
        lma.reply_message('請輸入年月\nex.202307', tk, ACCESS_TOKEN)
    elif text == "明細":
        firestore.update_firestore_field('Linebot_' + client + 'ID', ID, 'accounting_step', 'report')
        lma.reply_message('請輸入年月\nex.202307', tk, ACCESS_TOKEN)
