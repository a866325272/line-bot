"""OpenAI 對話模式 / 聊天 / DALL-E"""

from openai import OpenAI

from config import OPENAI_TOKEN, ACCESS_TOKEN, logger
import firestore
import lma


def chatmode(text: str, client: str, ID: str, tk: str):
    """對話模式處理"""
    if text[0:6] == '開始對話模式':
        lma.reply_message("對話模式已開始", tk, ACCESS_TOKEN)
    elif text[0:6] == '結束對話模式':
        firestore.update_firestore_field('Linebot_' + client + 'ID', ID, 'IsTalking', False)
        firestore.delete_firestore_field('Linebot_' + client + 'ID', ID, 'messages')
        lma.reply_message("對話模式已結束", tk, ACCESS_TOKEN)
    elif text[0:6] == '清空對話紀錄':
        firestore.delete_firestore_field('Linebot_' + client + 'ID', ID, 'messages')
        lma.reply_message("對話紀錄已清空", tk, ACCESS_TOKEN)
    else:
        lma.reply_message(_chat(text, client, ID), tk, ACCESS_TOKEN)


def _chat(input_text: str, client: str, ID: str) -> str:
    """呼叫 OpenAI chat API"""
    firestore.append_firestore_array_field(
        'Linebot_' + client + 'ID', ID, 'messages',
        [{"role": "user", "content": input_text}]
    )
    messages = firestore.get_firestore_field('Linebot_' + client + 'ID', ID, 'messages')
    logger.info(messages)
    openai_client = OpenAI(api_key=OPENAI_TOKEN)
    chat = openai_client.chat.completions.create(model="gpt-5", messages=messages)
    reply = chat.choices[0].message.content
    firestore.append_firestore_array_field(
        'Linebot_' + client + 'ID', ID, 'messages',
        [{"role": "assistant", "content": reply}]
    )
    return reply


def single_chat(text: str) -> str:
    """單次聊天（聊，指令）"""
    openai_client = OpenAI(api_key=OPENAI_TOKEN)
    response = openai_client.responses.create(
        model="gpt-5", input=text, tools=[{"type": "web_search"}]
    )
    return response.output_text


def dalle(msg: str) -> str:
    """DALL-E 製圖，回傳圖片 URL"""
    openai_client = OpenAI(api_key=OPENAI_TOKEN)
    draw = openai_client.images.generate(
        model="dall-e-3", prompt=msg, n=1, size="1024x1024"
    )
    return draw.data[0].url
