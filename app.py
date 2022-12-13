from flask import Flask, request
import requests, json, time
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage

app = Flask(__name__)

@app.route("/", methods=['POST'])

def linebot():
    body = request.get_data(as_text=True)                    # 取得收到的訊息內容
    try:
        json_data = json.loads(body)                         # json 格式化訊息內容
        access_token = '/mlAyjVDbf/FqLFbru0VTm8LFdBomUrgiOdGXSYSlIqGzIljiwMX138dGeihb6Wm0P9zvVsx3b1S+CXu9nvEHePeDz7pwlOTLXLi8YW7dj13tXetEn6guaBK9HUrQ7W9kH6Q//X0V+zQGTQiMLegYQdB04t89/1O/w1cDnyilFU='
        secret = 'c302c1e4e5a56f7ba87ee8b55691e44a'
        line_bot_api = LineBotApi(access_token)              # 確認 token 是否正確
        handler = WebhookHandler(secret)                     # 確認 secret 是否正確
        signature = request.headers['X-Line-Signature']      # 加入回傳的 headers
        handler.handle(body, signature)                      # 綁定訊息回傳的相關資訊
        tk = json_data['events'][0]['replyToken']            # 取得回傳訊息的 Token
        type = json_data['events'][0]['message']['type']     # 取得 LINe 收到的訊息類型
        if type=='text':
            msg = json_data['events'][0]['message']['text']  # 取得 LINE 收到的文字訊息
            if msg == '雷達回波圖' or msg == '雷達回波':
                print(0)
                message = f'https://cwbopendata.s3.ap-northeast-1.amazonaws.com/MSC/O-A0058-003.png?{time.time_ns()}'
                print(1)
                line_bot_api.reply_message(tk,ImageSendMessage(message,message))
                #reply_image(f'https://cwbopendata.s3.ap-northeast-1.amazonaws.com/MSC/O-A0058-003.png?{time.time_ns()}', tk, access_token)
            else:
                pass
                """print(msg)                                       # 印出內容
                reply = msg
                print(reply)
                line_bot_api.reply_message(tk,TextSendMessage(reply))# 回傳訊息"""
        else:
            pass
            """reply = '你傳的不是文字呦～'
            print(reply)
            line_bot_api.reply_message(tk,TextSendMessage(reply))# 回傳訊息"""
    except:
        print('error')
        #print(body)                                          # 如果發生錯誤，印出收到的內容
    return 'OK'                                              # 驗證 Webhook 使用，不能省略
#def hello_world():
#    return 'Hello, Docker!'

if __name__ == "__main__":
    app.run(host='0.0.0.0')

# LINE 回傳圖片函式
def reply_image(msg, rk, token):
    headers = {'Authorization':f'Bearer {token}','Content-Type':'application/json'}
    body = {
    'replyToken':rk,
    'messages':[{
          'type': 'image',
          'originalContentUrl': msg,
          'previewImageUrl': msg
        }]
    }
    req = requests.request('POST', 'https://api.line.me/v2/bot/message/reply', headers=headers,data=json.dumps(body).encode('utf-8'))
    print(req.text)
