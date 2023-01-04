from flask import Flask, request
import requests, json, time, statistics, numpy, os, openai
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage
from chatgpt import ChatGPT
from random import choice
from bs4 import BeautifulSoup
import random
epa_token = os.getenv('EPA_TOKEN')
cwb_token = os.getenv('CWB_TOKEN')
access_token = os.getenv('ACCESS_TOKEN')
secret = os.getenv('SECRET')
openai_token = os.getenv('OPENAI_TOKEN')
openai.api_key = openai_token

# 取得今日星座運勢
def get_luck(sign):
    json_zodiac = {"牡羊": "0", "金牛": "1", "雙子": "2", "巨蟹": "3", "獅子": "4", "處女": "5", "天秤": "6", "天蠍": "7", "射手": "8", "魔羯": "9", "水瓶": "10", "雙魚": "11"}
    url = "https://astro.click108.com.tw/daily.php?iAstro=" + json_zodiac[sign]
    web = requests.get(url)
    soup = BeautifulSoup(web.text, "html.parser")
    luck = soup.find_all("div", class_="TODAY_CONTENT")
    r = str(luck).replace('[<div class="TODAY_CONTENT">', "")
    r = r.replace("<h3>", "")
    r = r.replace("</h3>", "")
    r = r.replace('<p><span class="txt_green">', "")
    r = r.replace('<p><span class="txt_pink">', "")
    r = r.replace('<p><span class="txt_blue">', "")
    r = r.replace('<p><span class="txt_orange">', "")
    r = r.replace('</span></p><p>', "")
    r = r.replace('</p>', "")
    r = r.replace('</div>]', "")
    r = r.replace(f"\n今","今")
    return r

# 取得表特圖函式
def get_beauty():
    imgs = []
    n = random.randrange(1,901)
    for i in range(n,n+2,1):
        url = 'https://beautyptt.cc/extend?page=' + str(i)
        web = requests.get(url)
        soup = BeautifulSoup(web.text, "html.parser")
        links = soup.find_all("a")
        for link in links:
            if 'href' in link.attrs and 'imgur.com/' in link['href']:
                a = link['href']
                l = a.find('imgur.com/')
                a = a[l-2:l+18]
                imgs.append('https://'+a+'.jpg')
    img = choice(imgs)
    return(img)

# 取得迷因圖函式
def get_meme():
    imgs = []
    n = random.randrange(1,76)
    url = 'https://memes.tw/wtf/user/125281?page=' + str(n)
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'}
    web = requests.get(url, headers=headers)
    soup = BeautifulSoup(web.text, "html.parser")
    links = soup.find_all("img", class_="img-fluid lazy")
    for link in links:
        if 'data-src' in link.attrs:
            imgs.append(link['data-src'])
    img = choice(imgs)
    return img
    """headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'}
    m_data = requests.get('https://memes.tw/wtf/api', headers=headers)
    m_data_json = m_data.json()
    url = []
    for i in m_data_json:
        url.append(i['src'])
    img = choice(url)
    return img"""

# OpenAI製圖函式
def dalle(msg):
    headers = {'Authorization':f'Bearer {openai_token}','Content-Type':'application/json'}
    body = {
    "prompt": msg,
    "n": 1,
    "size": "256x256"
    }
    req = requests.request('POST', 'https://api.openai.com/v1/images/generations', headers=headers,data=json.dumps(body).encode('utf-8'))
    req_data_json = req.json()
    return req_data_json['data'][0]['url']

# 空氣品質函式
def aqi(address):
    city_list, site_list ={}, {}
    msg = '找不到空氣品質資訊。'
    try:
        url = f'https://data.epa.gov.tw/api/v2/aqx_p_432?limit=1000&api_key={epa_token}&sort=ImportDate%20desc&format=json'
        a_data = requests.get(url)             # 使用 get 方法透過空氣品質指標 API 取得內容
        a_data_json = a_data.json()            # json 格式化訊息內容
        #print(a_data_json)
        for i in a_data_json['records']:       # 依序取出 records 內容的每個項目
            city = i['county']                 # 取出縣市名稱
            if city not in city_list:
                city_list[city]=[]             # 以縣市名稱為 key，準備存入串列資料
            #site = i['sitename']               # 取出鄉鎮區域名稱
            if i['aqi'] != '':
                aqi = int(i['aqi'])                # 取得 AQI 數值
                #status = i['status']               # 取得空氣品質狀態
                #site_list[site] = {'aqi':aqi, 'status':status}  # 記錄鄉鎮區域空氣品質
                city_list[city].append(aqi)        # 將各個縣市裡的鄉鎮區域空氣 aqi 數值，以串列方式放入縣市名稱的變數裡
        for i in city_list:
            if i in address: # 如果地址裡包含縣市名稱的 key，就直接使用對應的內容
                # 參考 https://airtw.epa.gov.tw/cht/Information/Standard/AirQualityIndicator.aspx
                aqi_val = round(statistics.mean(city_list[i]),0)  # 計算平均數值，如果找不到鄉鎮區域，就使用縣市的平均值
                aqi_status = ''  # 手動判斷對應的空氣品質說明文字
                if aqi_val<=50: aqi_status = '良好'
                elif aqi_val>50 and aqi_val<=100: aqi_status = '普通'
                elif aqi_val>100 and aqi_val<=150: aqi_status = '對敏感族群不健康'
                elif aqi_val>150 and aqi_val<=200: aqi_status = '對所有族群不健康'
                elif aqi_val>200 and aqi_val<=300: aqi_status = '非常不健康'
                else: aqi_status = '危害'
                msg = i+f'空氣品質 :\n{aqi_status} ( AQI {aqi_val} )。' # 定義回傳的訊息
                break
        '''for i in site_list:
            if i in address:  # 如果地址裡包含鄉鎮區域名稱的 key，就直接使用對應的內容
                msg = i+f'空氣品質 :\n{site_list[i]["status"]} ( AQI {site_list[i]["aqi"]} )。'
                break'''
        return msg    # 回傳 msg
    except:
        return msg    # 如果取資料有發生錯誤，直接回傳 msg

# 氣象預報函式
def forecast(address):
    area_list = {}
    # 將主要縣市個別的 JSON 代碼列出
    json_api = {"宜蘭縣":"F-D0047-003","桃園市":"F-D0047-007","新竹縣":"F-D0047-011","苗栗縣":"F-D0047-015",
            "彰化縣":"F-D0047-019","南投縣":"F-D0047-023","雲林縣":"F-D0047-027","嘉義縣":"F-D0047-031",
            "屏東縣":"F-D0047-035","臺東縣":"F-D0047-039","花蓮縣":"F-D0047-043","澎湖縣":"F-D0047-047",
            "基隆市":"F-D0047-051","新竹市":"F-D0047-055","嘉義市":"F-D0047-059","臺北市":"F-D0047-063",
            "高雄市":"F-D0047-067","新北市":"F-D0047-071","臺中市":"F-D0047-075","臺南市":"F-D0047-079",
            "連江縣":"F-D0047-083","金門縣":"F-D0047-087"}
    msg = '找不到天氣預報資訊。'    # 預設回傳訊息
    try:
        url = f'https://opendata.cwb.gov.tw/fileapi/v1/opendataapi/F-C0032-001?Authorization={cwb_token}&downloadType=WEB&format=JSON'
        f_data = requests.get(url)   # 取得主要縣市預報資料
        f_data_json = f_data.json()  # json 格式化訊息內容
        location = f_data_json['cwbopendata']['dataset']['location']  # 取得縣市的預報內容
        for i in location:
            city = i['locationName']    # 縣市名稱
            #wx8 = i['weatherElement'][0]['time'][0]['parameter']['parameterName']    # 天氣現象
            #mint8 = i['weatherElement'][1]['time'][0]['parameter']['parameterName']  # 最低溫
            #maxt8 = i['weatherElement'][2]['time'][0]['parameter']['parameterName']  # 最高溫
            #ci8 = i['weatherElement'][2]['time'][0]['parameter']['parameterName']    # 舒適度
            #pop8 = i['weatherElement'][2]['time'][0]['parameter']['parameterName']   # 降雨機率
            area_list[city] = ''#f'未來 8 小時{wx8}，最高溫 {maxt8} 度，最低溫 {mint8} 度，降雨機率 {pop8} %，舒適度{ci8}'  # 組合成回傳的訊息，存在以縣市名稱為 key 的字典檔裡
        for i in area_list:
            if i in address:        # 如果使用者的地址包含縣市名稱
                msg = area_list[i]  # 將 msg 換成對應的預報資訊
                # 將進一步的預報網址換成對應的預報網址
                url = f'https://opendata.cwb.gov.tw/api/v1/rest/datastore/{json_api[i]}?Authorization={cwb_token}&elementName=WeatherDescription'
                f_data = requests.get(url)  # 取得主要縣市裡各個區域鄉鎮的氣象預報
                f_data_json = f_data.json() # json 格式化訊息內容
                location = f_data_json['records']['locations'][0]['location']    # 取得預報內容
                city = i
                break
        for i in location:
            area = i['locationName']   # 取得鄉鎮區域名稱
            starttime = i['weatherElement'][0]['time'][0]['startTime']
            endtime = i['weatherElement'][0]['time'][0]['endTime']
            wd = i['weatherElement'][0]['time'][0]['elementValue'][0]['value']  # 綜合描述
            starttime1 = i['weatherElement'][0]['time'][1]['startTime']
            endtime1 = i['weatherElement'][0]['time'][1]['endTime']           
            wd1 = i['weatherElement'][0]['time'][1]['elementValue'][0]['value']  # 綜合描述
            starttime2 = i['weatherElement'][0]['time'][2]['startTime']
            endtime2 = i['weatherElement'][0]['time'][2]['endTime']           
            wd2 = i['weatherElement'][0]['time'][2]['elementValue'][0]['value']  # 綜合描述
            starttime3 = i['weatherElement'][0]['time'][3]['startTime']
            endtime3 = i['weatherElement'][0]['time'][3]['endTime']           
            wd3 = i['weatherElement'][0]['time'][3]['elementValue'][0]['value']  # 綜合描述
            if area in address:           # 如果使用者的地址包含鄉鎮區域名稱
                msg = city+area+f'天氣預報 :\n{starttime}~\n{endtime}\n{wd}\n\n{starttime1}~\n{endtime1}\n{wd1}\n\n{starttime2}~\n{endtime2}\n{wd2}\n\n{starttime3}~\n{endtime3}\n{wd3}' # 將 msg 換成對應的預報資訊
                break
        return msg  # 回傳 msg
    except:
        return msg  # 如果取資料有發生錯誤，直接回傳 msg

# 目前天氣函式
def current_weather(address):
    city_list, city_list2, area_list, area_list2 = {}, {}, {}, {} # 定義好待會要用的變數
    msg = '找不到氣象資訊。'                         # 預設回傳訊息

    # 定義取得資料的函式
    def get_data(url):
        w_data = requests.get(url)   # 爬取目前天氣網址的資料
        w_data_json = w_data.json()  # json 格式化訊息內容
        location = w_data_json['cwbopendata']['location']  # 取出對應地點的內容
        for i in location:
            #name = i['locationName']                       # 測站地點
            city = i['parameter'][0]['parameterValue']     # 縣市名稱
            area = i['parameter'][2]['parameterValue']     # 鄉鎮行政區
            city_area = city + area
            temp = check_data(i['weatherElement'][3]['elementValue']['value'])                       # 氣溫
            humd = check_data(round(float(i['weatherElement'][4]['elementValue']['value'] )*100 ,1)) # 相對濕度
            r24 = check_data(i['weatherElement'][6]['elementValue']['value'])                        # 累積雨量

            if city_area not in area_list:
                area_list[city_area] = {'temp':[], 'humd':[], 'r24':[], 'wx':[]}      # 以鄉鎮區域為 key，儲存需要的資訊
            if city not in city_list:
                city_list[city] = {'temp':[], 'humd':[], 'r24':[]}      # 以主要縣市名稱為 key，準備紀錄裡面所有鄉鎮的數值
            city_list[city]['temp'].append(temp)   # 記錄主要縣市裡鄉鎮區域的溫度 ( 串列格式 )
            city_list[city]['humd'].append(humd)   # 記錄主要縣市裡鄉鎮區域的濕度 ( 串列格式 )
            city_list[city]['r24'].append(r24)     # 記錄主要縣市裡鄉鎮區域的雨量 ( 串列格式 )
            area_list[city_area]['temp'].append(temp)   # 記錄鄉鎮區域的溫度 ( 串列格式 )
            area_list[city_area]['humd'].append(humd)   # 記錄鄉鎮區域的濕度 ( 串列格式 )
            area_list[city_area]['r24'].append(r24)     # 記錄鄉鎮區域的雨量 ( 串列格式 )
            if 'O-A0003-001' in url:
                wx = i['weatherElement'][20]['elementValue']['value']
                area_list[city_area]['wx'].append(wx)       # 記錄鄉鎮區域的天氣描述 ( 串列格式 )


    # 定義如果數值小於 0，回傳 nan 的函式
    def check_data(e):
        return numpy.nan if float(e)<0 else float(e)

    # 定義產生回傳訊息的函式
    def msg_content(loc, msg):
        a = msg
        for i in loc:
            if i in address: # 如果地址裡存在 key 的名稱
                wx = ""
                temp = f"氣溫 {loc[i]['temp']} 度，" if loc[i]['temp'] != None else ''
                humd = f"相對濕度 {loc[i]['humd']}%，" if loc[i]['humd'] != None else ''
                r24 = f"累積雨量 {loc[i]['r24']}mm，" if loc[i]['r24'] != None else ''
                if len(loc[i])==4 and loc[i]['wx'] != []:
                    wx = f"{loc[i]['wx'][0]}，"

                description = i+f'目前天氣 :\n{wx}{temp}{humd}{r24}'.strip('，')
                a = f'{description}。' # 取出 key 的內容作為回傳訊息使用
                break
        return a

    try:
        # 因為目前天氣有兩組網址，兩組都爬取
        get_data(f'https://opendata.cwb.gov.tw/fileapi/v1/opendataapi/O-A0001-001?Authorization={cwb_token}&downloadType=WEB&format=JSON')
        get_data(f'https://opendata.cwb.gov.tw/fileapi/v1/opendataapi/O-A0003-001?Authorization={cwb_token}&downloadType=WEB&format=JSON')
        for i in city_list:
            if i not in city_list2: # 將主要縣市裡的數值平均後，以主要縣市名稱為 key，再度儲存一次，如果找不到鄉鎮區域，就使用平均數值
                city_list2[i] = {'temp':round(numpy.nanmean(city_list[i]['temp']),1),
                                'humd':round(numpy.nanmean(city_list[i]['humd']),1),
                                'r24':round(numpy.nanmean(city_list[i]['r24']),1)
                                }
        for i in area_list:
            if i not in area_list2: # 將鄉鎮區域裡的數值平均後，以鄉鎮區域名稱為 key，使用平均數值
                area_list2[i] = {'temp':round(numpy.nanmean(area_list[i]['temp']),1),
                                'humd':round(numpy.nanmean(area_list[i]['humd']),1),
                                'r24':round(numpy.nanmean(area_list[i]['r24']),1),
                                'wx':area_list[i]['wx']
                                }
        msg = msg_content(city_list2, msg)  # 將訊息改為「大縣市」
        msg = msg_content(area_list2, msg)   # 將訊息改為「鄉鎮區域」
        return msg    # 回傳 msg
    except:
        return msg    # 如果取資料有發生錯誤，直接回傳 msg

# 地震資訊函式
def earth_quake():
    msg = ['找不到地震資訊','https://example.com/demo.jpg']             # 預設回傳的訊息
    try:
        url = f'https://opendata.cwb.gov.tw/api/v1/rest/datastore/E-A0016-001?Authorization={cwb_token}'
        url2 = f'https://opendata.cwb.gov.tw/api/v1/rest/datastore/E-A0015-001?Authorization={cwb_token}'
        e_data = requests.get(url)                                      # 爬取區域地震資訊網址
        e_data_json = e_data.json()                                     # json 格式化訊息內容
        e_data2 = requests.get(url2)                                    # 爬取有感地震資訊網址
        e_data_json2 = e_data2.json()                                   # json 格式化訊息內容
        eq = e_data_json['records']['Earthquake']                       # 取出區域地震資訊
        eq2 = e_data_json2['records']['Earthquake']                     # 取出有感地震資訊
        for i in eq:
            loc = i['EarthquakeInfo']['Epicenter']['Location']          # 地震地點
            val = i['EarthquakeInfo']['EarthquakeMagnitude']['MagnitudeValue']    # 地震規模
            dep = i['EarthquakeInfo']['FocalDepth']                     # 地震深度
            eq_time = i['EarthquakeInfo']['OriginTime']                                   # 地震時間
            img = i['ReportImageURI']                                   # 地震圖
            #msg = [f'{loc}，芮氏規模 {val} 級，深度 {dep} 公里，發生時間 {eq_time}。', img]
            break                                                       # 取出第一筆資料後就 break
        for i in eq2:
            loc2 = i['EarthquakeInfo']['Epicenter']['Location']         # 地震地點
            val2 = i['EarthquakeInfo']['EarthquakeMagnitude']['MagnitudeValue']   # 地震規模
            dep2 = i['EarthquakeInfo']['FocalDepth']                    # 地震深度
            eq_time2 = i['EarthquakeInfo']['OriginTime']                                  # 地震時間
            img2 = i['ReportImageURI']                                  # 地震圖
            #msg = [f'{loc}，芮氏規模 {val} 級，深度 {dep} 公里，發生時間 {eq_time}。', img]
            break                                                       # 取出第一筆資料後就 break
        if eq_time > eq_time2:                                          # 判斷最近一筆時間資料回傳
            msg = [f'{loc}，芮氏規模 {val} 級，深度 {dep} 公里，發生時間 {eq_time}。', img]
        else:
            msg = [f'{loc2}，芮氏規模 {val2} 級，深度 {dep2} 公里，發生時間 {eq_time2}。', img2]
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
    print("reply_img:"+msg)

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
    print("reply_message:"+msg)

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
    print("push_msg:"+msg)

app = Flask(__name__)

@app.route("/", methods=['POST'])

def linebot():
    body = request.get_data(as_text=True)                       # 取得收到的訊息內容
    try:
        json_data = json.loads(body)                            # json 格式化訊息內容
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
            reply_message(f'{current_weather(address)}\n\n{aqi(address)}\n\n{forecast(address)}', tk, access_token)
        if type=='text':
            text = json_data['events'][0]['message']['text']     # 取得 LINE 收到的文字訊息
            if text == '雷達回波圖' or text == '雷達回波':
                reply_image(f'https://cwbopendata.s3.ap-northeast-1.amazonaws.com/MSC/O-A0058-003.png?{time.time_ns()}', tk, access_token)
            elif text == '地震資訊' or text == '地震':
                quake = earth_quake()                           # 爬取地震資訊
                push_message(quake[0], group_id, access_token)  # 傳送地震資訊 ( 用 push 方法，因為 reply 只能用一次 )
                reply_image(quake[1], tk, access_token)         # 傳送地震圖片 ( 用 reply 方法 )
            elif text[0:2] == '畫，' or text[0:2] == '畫,':
                openai_image_url = dalle(text[2:])
                reply_image(openai_image_url, tk, access_token)
            elif text[0:2] == '聊，' or text[0:2] == '聊,':
                chatgpt = ChatGPT()
                chatgpt.add_msg(f"Human:{text[2:]}\n")
                reply_msg = chatgpt.get_response().replace("AI:", "", 1)
                reply_message(reply_msg , tk, access_token)
            elif text == '扛' or text == '坦':
                reply_image(get_meme(), tk, access_token)
            elif text == '抽':
                reply_image(get_beauty(), tk, access_token)
            elif text == '!help' or text == '！help':
                reply_msg = f'指令說明\n扛 或 坦- 打了你就知道啦~~\n抽 - 抽美女帥哥圖\n聊， - 機器人陪你聊天\n畫， - 機器人合成圖片\n地震 - 傳送最近一筆地震資訊\n雷達回波 - 傳送衛星雲圖\n發送位置 - 回報天氣資訊和預報\n星座 例如:處女  - 回報運勢'
                reply_message(reply_msg , tk, access_token)
            elif text == '牡羊' or '金牛' or '雙子' or '巨蟹' or '獅子' or '處女' or '天秤' or '天蠍' or '射手' or '魔羯' or '水瓶' or '雙魚':
                reply_message(get_luck(text), tk, access_token)
            else:
                pass
                """print(msg)                                       # 印出內容
                reply = msg
                print(reply)
                line_bot_api.reply_message(tk,TextSendMessage(reply))# 回傳訊息"""
    except:
        print('error')                                          # 如果發生錯誤，印出error                                   
    return 'OK'                                                 # 驗證 Webhook 使用，不能省略

if __name__ == "__main__":
    app.run(host='0.0.0.0')
