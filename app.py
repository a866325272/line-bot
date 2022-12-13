from flask import Flask, request
import requests, json, time, statistics
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage

# 目前天氣函式
def current_weather(address):
    city_list, area_list, area_list2 = {}, {}, {} # 定義好待會要用的變數
    msg = '找不到氣象資訊。'                         # 預設回傳訊息

    # 定義取得資料的函式
    def get_data(url):
        w_data = requests.get(url)   # 爬取目前天氣網址的資料
        w_data_json = w_data.json()  # json 格式化訊息內容
        location = w_data_json['cwbopendata']['location']  # 取出對應地點的內容
        for i in location:
            name = i['locationName']                       # 測站地點
            city = i['parameter'][0]['parameterValue']     # 縣市名稱
            area = i['parameter'][2]['parameterValue']     # 鄉鎮行政區
            temp = check_data(i['weatherElement'][3]['elementValue']['value'])                       # 氣溫
            humd = check_data(round(float(i['weatherElement'][4]['elementValue']['value'] )*100 ,1)) # 相對濕度
            r24 = check_data(i['weatherElement'][6]['elementValue']['value'])                        # 累積雨量
            if area not in area_list:
                area_list[area] = {'temp':temp, 'humd':humd, 'r24':r24}  # 以鄉鎮區域為 key，儲存需要的資訊
            if city not in city_list:
                city_list[city] = {'temp':[], 'humd':[], 'r24':[]}       # 以主要縣市名稱為 key，準備紀錄裡面所有鄉鎮的數值
            city_list[city]['temp'].append(temp)   # 記錄主要縣市裡鄉鎮區域的溫度 ( 串列格式 )
            city_list[city]['humd'].append(humd)   # 記錄主要縣市裡鄉鎮區域的濕度 ( 串列格式 )
            city_list[city]['r24'].append(r24)     # 記錄主要縣市裡鄉鎮區域的雨量 ( 串列格式 )

    # 定義如果數值小於 0，回傳 False 的函式
    def check_data(e):
        return False if float(e)<0 else float(e)

    # 定義產生回傳訊息的函式
    def msg_content(loc, msg):
        a = msg
        for i in loc:
            if i in address: # 如果地址裡存在 key 的名稱
                temp = f"氣溫 {loc[i]['temp']} 度，" if loc[i]['temp'] != False else ''
                humd = f"相對濕度 {loc[i]['humd']}%，" if loc[i]['humd'] != False else ''
                r24 = f"累積雨量 {loc[i]['r24']}mm" if loc[i]['r24'] != False else ''
                description = f'{temp}{humd}{r24}'.strip('，')
                a = f'{description}。' # 取出 key 的內容作為回傳訊息使用
                break
        return a

    try:
        # 因為目前天氣有兩組網址，兩組都爬取
        code = 'CWB-5C79FBC7-F8B2-42F1-B127-20D65DBF3EBB'
        get_data(f'https://opendata.cwb.gov.tw/fileapi/v1/opendataapi/O-A0001-001?Authorization={code}&downloadType=WEB&format=JSON')
        get_data(f'https://opendata.cwb.gov.tw/fileapi/v1/opendataapi/O-A0003-001?Authorization={code}&downloadType=WEB&format=JSON')

        for i in city_list:
            if i not in area_list2: # 將主要縣市裡的數值平均後，以主要縣市名稱為 key，再度儲存一次，如果找不到鄉鎮區域，就使用平均數值
                area_list2[i] = {'temp':round(statistics.mean(city_list[i]['temp']),1),
                                'humd':round(statistics.mean(city_list[i]['humd']),1),
                                'r24':round(statistics.mean(city_list[i]['r24']),1)
                                }
        msg = msg_content(area_list2, msg)  # 將訊息改為「大縣市」
        msg = msg_content(area_list, msg)   # 將訊息改為「鄉鎮區域」
        return msg    # 回傳 msg
    except:
        return msg    # 如果取資料有發生錯誤，直接回傳 msg

# 地震資訊函式
def earth_quake():
    msg = ['找不到地震資訊','https://example.com/demo.jpg']             # 預設回傳的訊息
    try:
        code = 'CWB-5C79FBC7-F8B2-42F1-B127-20D65DBF3EBB'
        url = f'https://opendata.cwb.gov.tw/api/v1/rest/datastore/E-A0016-001?Authorization={code}'
        e_data = requests.get(url)                                      # 爬取地震資訊網址
        e_data_json = e_data.json()                                     # json 格式化訊息內容
        eq = e_data_json['records']['earthquake']                       # 取出地震資訊
        for i in eq:
            loc = i['earthquakeInfo']['epiCenter']['location']          # 地震地點
            val = i['earthquakeInfo']['magnitude']['magnitudeValue']    # 地震規模
            dep = i['earthquakeInfo']['depth']['value']                 # 地震深度
            eq_time = i['earthquakeInfo']['originTime']                 # 地震時間
            img = i['reportImageURI']                                   # 地震圖
            msg = [f'{loc}，芮氏規模 {val} 級，深度 {dep} 公里，發生時間 {eq_time}。', img]
            break                                                       # 取出第一筆資料後就 break
        return msg                                                      # 回傳 msg
    except:
        return msg                                                      # 如果取資料有發生錯誤，直接回傳 msg

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
    print("reply_img:"+req.text)

# LINE 回傳訊息函式
def reply_message(msg, rk, token):
    headers = {'Authorization':f'Bearer {token}','Content-Type':'application/json'}
    body = {
    'replyToken':rk,
    'messages':[{
            "type": "text",
            "text": msg
        }]
    }
    req = requests.request('POST', 'https://api.line.me/v2/bot/message/reply', headers=headers,data=json.dumps(body).encode('utf-8'))
    print(req.text)

# LINE push 訊息函式
def push_message(msg, uid, token):
    headers = {'Authorization':f'Bearer {token}','Content-Type':'application/json'}   
    body = {
    'to':uid,
    'messages':[{
            "type": "text",
            "text": msg
        }]
    }
    req = requests.request('POST', 'https://api.line.me/v2/bot/message/push', headers=headers,data=json.dumps(body).encode('utf-8'))
    print("push_msg:"+req.text)

app = Flask(__name__)

@app.route("/", methods=['POST'])

def linebot():
    body = request.get_data(as_text=True)                       # 取得收到的訊息內容
    try:
        json_data = json.loads(body)                            # json 格式化訊息內容
        access_token = '/mlAyjVDbf/FqLFbru0VTm8LFdBomUrgiOdGXSYSlIqGzIljiwMX138dGeihb6Wm0P9zvVsx3b1S+CXu9nvEHePeDz7pwlOTLXLi8YW7dj13tXetEn6guaBK9HUrQ7W9kH6Q//X0V+zQGTQiMLegYQdB04t89/1O/w1cDnyilFU='
        secret = 'c302c1e4e5a56f7ba87ee8b55691e44a'
        #line_bot_api = LineBotApi(access_token)                 # 確認 token 是否正確
        handler = WebhookHandler(secret)                        # 確認 secret 是否正確
        signature = request.headers['X-Line-Signature']         # 加入回傳的 headers
        handler.handle(body, signature)                         # 綁定訊息回傳的相關資訊
        tk = json_data['events'][0]['replyToken']               # 取得回傳訊息的 Token
        #user_id = json_data['events'][0]['source']['userId']    # 取得發出請求的UserID
        group_id = json_data['events'][0]['source']['groupId']  # 取得發出請求的GroupID
        type = json_data['events'][0]['message']['type']        # 取得 LINe 收到的訊息類型
        if type=='location':
            address = json_data['events'][0]['message']['address'].replace('台','臺')   # 取出地址資訊，並將「台」換成「臺」
            reply_message(f'{address}\n\n{current_weather(address)}', tk, access_token)
            print(address)
        if type=='text':
            text = json_data['events'][0]['message']['text']     # 取得 LINE 收到的文字訊息
            if text == '雷達回波圖' or text == '雷達回波':
                #message = f'https://cwbopendata.s3.ap-northeast-1.amazonaws.com/MSC/O-A0058-003.png?{time.time_ns()}'
                #line_bot_api.reply_message(tk,ImageSendMessage(message,message))
                reply_image(f'https://cwbopendata.s3.ap-northeast-1.amazonaws.com/MSC/O-A0058-003.png?{time.time_ns()}', tk, access_token)
            elif text == '地震資訊' or text == '地震':
                quake = earth_quake()                           # 爬取地震資訊
                push_message(quake[0], group_id, access_token)  # 傳送地震資訊 ( 用 push 方法，因為 reply 只能用一次 )
                reply_image(quake[1], tk, access_token)         # 傳送地震圖片 ( 用 reply 方法 )
                #line_bot_api.reply_message(tk, ImageSendMessage(quake[1],quake[1]))          # 傳送地震圖片 ( 用 reply 方法 )
            else:
                pass
                """print(msg)                                       # 印出內容
                reply = msg
                print(reply)
                line_bot_api.reply_message(tk,TextSendMessage(reply))# 回傳訊息"""
        """else:
            pass
            reply = '你傳的不是文字呦～'
            print(reply)
            line_bot_api.reply_message(tk,TextSendMessage(reply))# 回傳訊息"""
    except:
        print('error')                                          # 如果發生錯誤，印出error                                   
    return 'OK'                                                 # 驗證 Webhook 使用，不能省略

if __name__ == "__main__":
    app.run(host='0.0.0.0')
