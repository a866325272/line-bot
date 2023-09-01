from google.cloud import firestore
from flask import Flask, request
from linebot import WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage
from random import choice
from bs4 import BeautifulSoup
from logging.handlers import TimedRotatingFileHandler
from dotenv import load_dotenv
from datetime import timezone, timedelta, datetime
from matplotlib import pyplot as plt
import google.cloud.texttospeech as tts
import datetime as dt
import requests, json, time, statistics, numpy, os, openai, random, logging
load_dotenv()
epa_token = os.getenv('EPA_TOKEN')
cwb_token = os.getenv('CWB_TOKEN')
access_token = os.getenv('ACCESS_TOKEN')
secret = os.getenv('SECRET')
openai_token = os.getenv('OPENAI_TOKEN')
log_path = os.getenv('LOG_PATH')
import firestore    # firestore operations
import gcs          # gcs operations
import gss
openai.api_key = openai_token

# log config
logger = logging.getLogger('')
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
rotate_handler = logging.handlers.TimedRotatingFileHandler(log_path+'line-bot.log',when="h",interval=1,backupCount=720)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
rotate_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
logger.addHandler(rotate_handler)
logger.addHandler(console_handler)

# 月帳統計
def account_monthly(client, ID, date):
    #tz = timezone(timedelta(hours=+8))
    #today = datetime.now(tz)
    #date = today.strftime("%Y_%m_%d")
    accounts = firestore.get_firestore_field('Linebot_'+client+'ID',ID,'Accounts_'+date[:7])
    cost_summation = [0,0,0,0,0,0,0,0]
    income_summation = 0
    for account in accounts:
        for i in range(8):
            if account['Type'] == i+1:
                cost_summation[i] += account['Ammount']
        if account['Type'] == 11:
            income_summation += account['Ammount']
    return [cost_summation,income_summation]

# 生成圓餅圖
def pie_chart(index: list, value: list, title: str):
    # Filter out 0% values
    non_zero_data = [d for d in value if d != 0]
    non_zero_labels = [l for d, l in zip(value, index) if d != 0]
    res = ['0.0%','0.0%','0.0%','0.0%','0.0%','0.0%','0.0%','0.0%']
    # Creating plot
    fig = plt.figure(figsize =(10, 7))
    patches, labels, percentages = plt.pie(non_zero_data, labels = non_zero_labels, autopct='%1.1f%%', textprops={'fontsize': 24})
    percentage_values = [p.get_text() for p in percentages]
    label_values = [l.get_text() for l in labels]
    for l in zip(label_values,percentage_values):
        res[index.index(l[0])] = l[1]
    plt.rcParams['font.sans-serif'] = 'WenQuanYi Zen Hei'
    # Set the figure title
    plt.title(title, fontsize=24)
    # Adjusting padding
    plt.tight_layout(pad=0)
    # download plot
    plt.savefig('accounts-pie-chart.png')
    return res

# 文字轉語音
def text_to_speech(voice_name: str, text: str):
    language_code = "-".join(voice_name.split("-")[:2])
    text_input = tts.SynthesisInput(text=text)
    voice_params = tts.VoiceSelectionParams(
        language_code=language_code, name=voice_name
    )
    audio_config = tts.AudioConfig(audio_encoding=tts.AudioEncoding.LINEAR16)

    client = tts.TextToSpeechClient()
    response = client.synthesize_speech(
        input=text_input,
        voice=voice_params,
        audio_config=audio_config,
    )

    filename = "text-to-speech.wav"
    with open(filename, "wb") as out:
        out.write(response.audio_content)

# 取得新聞
def news(cat: str):
    if cat == "焦點新聞":
        url = "https://news.google.com/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNRFZxYUdjU0JYcG9MVlJYR2dKVVZ5Z0FQAQ?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant"
    elif cat == "國際新聞":
        url = "https://news.google.com/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNRGx1YlY4U0JYcG9MVlJYR2dKVVZ5Z0FQAQ?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant"
    elif cat == "商業新聞":
        url = "https://news.google.com/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNRGx6TVdZU0JYcG9MVlJYR2dKVVZ5Z0FQAQ?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant"
    elif cat == "科技新聞":
        url = "https://news.google.com/topics/CAAqLAgKIiZDQkFTRmdvSkwyMHZNR1ptZHpWbUVnVjZhQzFVVnhvQ1ZGY29BQVAB?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant"
    elif cat == "體育新聞":
        url = "https://news.google.com/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNRFp1ZEdvU0JYcG9MVlJYR2dKVVZ5Z0FQAQ?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant"
    elif cat == "娛樂新聞":
        url = "https://news.google.com/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNREpxYW5RU0JYcG9MVlJYR2dKVVZ5Z0FQAQ?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant"
    web = requests.get(url)
    soup = BeautifulSoup(web.text, "html.parser")
    tags = soup.select(".IBr9hb a")
    links = []
    for i in range(5):
        url = "https://news.google.com/"+tags[i]['href'][2::]
        web = requests.get(url, allow_redirects=False)
        links.append(web.headers['Location'])
    #縮網址
    short_links = []
    titles = []
    url = "https://tinyurl.com/api-create.php?url="
    for i in links:
        req = requests.request("GET", url+i)
        short_links.append(req.text)
    #取得標題
    for i in short_links:
        url = i
        req = requests.get(url)
        title_start = req.text.find("<title>")
        title_end = req.text.find("</title>", title_start)
        title = req.text[title_start + 7:title_end].strip()
        titles.append(title)
    content = {"type":"carousel","contents":[{"type":"bubble","size": "micro","body":{"type":"box","layout":"vertical","spacing":"sm","contents":[{"type":"text","wrap":True,"weight":"bold","size":"sm","text":titles[0]}]},"footer":{"type":"box","layout":"vertical","spacing":"sm","contents":[{"type":"button","style":"primary","action":{"type":"uri","label":"前往連結","uri":short_links[0]},"height": "sm"}]}},{"type":"bubble","size": "micro","body":{"type":"box","layout":"vertical","spacing":"sm","contents":[{"type":"text","wrap":True,"weight":"bold","size":"sm","text":titles[1]}]},"footer":{"type":"box","layout":"vertical","spacing":"sm","contents":[{"type":"button","style":"primary","action":{"type":"uri","label":"前往連結","uri":links[1]},"height": "sm"}]}},{"type":"bubble","size": "micro","body":{"type":"box","layout":"vertical","spacing":"sm","contents":[{"type":"text","wrap":True,"weight":"bold","size":"sm","text":titles[2]}]},"footer":{"type":"box","layout":"vertical","spacing":"sm","contents":[{"type":"button","style":"primary","action":{"type":"uri","label":"前往連結","uri":short_links[2]},"height": "sm"}]}},{"type":"bubble","size": "micro","body":{"type":"box","layout":"vertical","spacing":"sm","contents":[{"type":"text","wrap":True,"weight":"bold","size":"sm","text":titles[3]}]},"footer":{"type":"box","layout":"vertical","spacing":"sm","contents":[{"type":"button","style":"primary","action":{"type":"uri","label":"前往連結","uri":short_links[3]},"height": "sm"}]}},{"type":"bubble","size": "micro","body":{"type":"box","layout":"vertical","spacing":"sm","contents":[{"type":"text","wrap":True,"weight":"bold","size":"sm","text":titles[4]}]},"footer":{"type":"box","layout":"vertical","spacing":"sm","contents":[{"type":"button","style":"primary","action":{"type":"uri","label":"前往連結","uri":short_links[4]},"height": "sm"}]}}]}
    return content

# 對話模式
def chatmode(input: str,client: str,ID: str) -> str:
    firestore.append_firestore_array_field('Linebot_'+client+'ID',ID,'messages',[{"role": "user", "content": input}])
    messages = firestore.get_firestore_field('Linebot_'+client+'ID',ID,'messages')
    logger.info(messages)
    chat = openai.ChatCompletion.create(
        model="gpt-4", messages=messages
    )
    reply = chat.choices[0].message.content
    firestore.append_firestore_array_field('Linebot_'+client+'ID',ID,'messages',[{"role": "assistant", "content": reply}])
    return reply

# 取得加密貨幣交易對列表
def get_cryptocurrency_market():
    msg=''
    data = requests.get('https://max-api.maicoin.com/api/v2/markets')
    json_data = data.json()
    for i in json_data:
        msg += f'id:{i["id"]},交易對:{i["name"]}\n'
    msg = msg[0:len(msg)-1]
    return(msg)

# 取得加密貨幣價格
def cryptocurrency(market):
    try:
        trades = requests.get(f'https://max-api.maicoin.com/api/v2/trades?market={market}') #取得成交列表
        trades_data = trades.json()
        timestamp = trades_data[0]['created_at']
        datetime_obj = dt.datetime.fromtimestamp(timestamp)
        price = trades_data[0]['price']
        volume = trades_data[0]['volume']
        market_name = trades_data[0]['market_name']
        side = trades_data[0]['side']
        if side == 'bid':
            side = '賣'
        elif side == 'ask':
            side = '買'

        depth = requests.get(f'https://max-api.maicoin.com/api/v2/depth?market={market}')   #取得掛單簿
        depth_data = depth.json()
        ask_price = depth_data['asks'][-1][0]
        ask_volume = depth_data['asks'][-1][1]
        bid_price = depth_data['bids'][0][0]
        bid_volume = depth_data['bids'][0][1]

        msg = f'{market_name} 最新成交({side}):\n成交時間:{datetime_obj}\n成交價:{price}\t成交量:{volume}\n{market_name} 掛單簿:\n賣 價格:{ask_price}\t數量:{ask_volume}\n買 價格:{bid_price}\t數量:{bid_volume}'
        return msg
    except:
        return "格式錯誤"

# 語音轉文字
def speech_to_text(message_id) -> str:
    headers = {'Authorization':f'Bearer {access_token}'}
    req = requests.request('GET', f'https://api-data.line.me/v2/bot/message/{message_id}/content', headers=headers)
    open("temp.wav","wb").write(req.content)
    f = open("temp.wav", "rb")
    transcript = openai.Audio.transcribe("whisper-1", f)
    tr_json = json.loads(str(transcript))
    return tr_json['text']

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
    r = r[0:len(r)-1]
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
            #starttime = i['weatherElement'][0]['time'][0]['startTime']
            endtime = i['weatherElement'][0]['time'][0]['endTime']
            if endtime[11] == '0' and endtime[12] == '6':
                endtime = endtime[:11] + "0時"
            if endtime[11] == '1' and endtime[12] == '8':
                endtime = endtime[:11] + "12時"
            wd = i['weatherElement'][0]['time'][0]['elementValue'][0]['value']  # 綜合描述
            #starttime1 = i['weatherElement'][0]['time'][1]['startTime']
            endtime1 = i['weatherElement'][0]['time'][1]['endTime']
            if endtime1[11] == '0' and endtime1[12] == '6':
                endtime1 = endtime1[:11] + "0時"
            if endtime1[11] == '1' and endtime1[12] == '8':
                endtime1 = endtime1[:11] + "12時"
            wd1 = i['weatherElement'][0]['time'][1]['elementValue'][0]['value']  # 綜合描述
            #starttime2 = i['weatherElement'][0]['time'][2]['startTime']
            #endtime2 = i['weatherElement'][0]['time'][2]['endTime']
            #if endtime2[11] == '0' and endtime2[12] == '6':
            #    endtime2 = endtime2[:11] + "0時"
            #if endtime2[11] == '1' and endtime2[12] == '8':
            #    endtime2 = endtime2[:11] + "12時"
            #wd2 = i['weatherElement'][0]['time'][2]['elementValue'][0]['value']  # 綜合描述
            #starttime3 = i['weatherElement'][0]['time'][3]['startTime']
            #endtime3 = i['weatherElement'][0]['time'][3]['endTime']
            #if endtime3[11] == '0' and endtime3[12] == '6':
            #    endtime3 = endtime3[:11] + "0時"
            #if endtime3[11] == '1' and endtime3[12] == '8':
            #    endtime3 = endtime3[:11] + "12時"
            #wd3 = i['weatherElement'][0]['time'][3]['elementValue'][0]['value']  # 綜合描述
            if area in address:           # 如果使用者的地址包含鄉鎮區域名稱
                msg = city+area+f'天氣預報 :\n{endtime}\n{wd}\n\n{endtime1}\n{wd1}' # 將 msg 換成對應的預報資訊
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
    logger.info("reply_img:"+msg)

# LINE 回傳語音函式
def reply_audio(msg, rk, token):
    headers = {'Authorization':f'Bearer {token}','Content-Type':'application/json'}
    body = {
    'replyToken':rk,
    'messages':[{
          'type': 'audio',
          'originalContentUrl': msg,
          'duration': '600000'
        }]
    }
    req = requests.request('POST', 'https://api.line.me/v2/bot/message/reply', headers=headers,data=json.dumps(body).encode('utf-8'))
    logger.info("reply_audio:"+msg)

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
    logger.info("reply_msg:"+msg)

# LINE push 訊息函式
def push_message(msg, ID, token):
    headers = {'Authorization':f'Bearer {token}','Content-Type':'application/json'}   
    body = {
    'to':ID,
    'messages':[{
            "type": "text",
            "text": msg
        }]
    }
    req = requests.request('POST', 'https://api.line.me/v2/bot/message/push', headers=headers,data=json.dumps(body).encode('utf-8'))
    logger.info("push_msg:"+msg)

# LINE 回傳flex訊息
def reply_flex_message(msg, content, rk, token):
    headers = {'Authorization':f'Bearer {token}','Content-Type':'application/json'}
    body = {
    'replyToken':rk,
    'messages':[{
            "type": "flex",
            "altText": msg,
            "contents": content
        }]
    }
    req = requests.request('POST', 'https://api.line.me/v2/bot/message/reply', headers=headers,data=json.dumps(body).encode('utf-8'))
    logger.info("reply_flex_msg:"+msg)

app = Flask(__name__)

@app.route("/", methods=['POST'])

def linebot():
    body = request.get_data(as_text=True)                       # 取得收到的訊息內容
    try:
        json_data = json.loads(body)                            # json 格式化訊息內容
        handler = WebhookHandler(secret)                        # 確認 secret 是否正確
        signature = request.headers['X-Line-Signature']         # 加入回傳的 headers
        handler.handle(body, signature)                         # 綁定訊息回傳的相關資訊
        tk = json_data['events'][0]['replyToken']               # 取得回傳訊息的 Token       
        user_id = json_data['events'][0]['source']['userId']    # 取得發出請求的UserID
        client = "User"
        ID = user_id
        try:
            group_id = json_data['events'][0]['source']['groupId']  # 取得發出請求的GroupID
            client = "Group"
            ID = group_id
        except:
            pass
        type = json_data['events'][0]['message']['type']        # 取得 LINe 收到的訊息類型
        if type=='location':
            address = json_data['events'][0]['message']['address'].replace('台','臺')   # 取出地址資訊，並將「台」換成「臺」
            reply_message(f'{current_weather(address)}\n\n{aqi(address)}\n\n{forecast(address)}', tk, access_token)
        if type=='text':
            text = json_data['events'][0]['message']['text']     # 取得 LINE 收到的文字訊息
            logger.info(text)
            if firestore.get_firestore_field('Linebot_'+client+'ID',ID,'IsTalking'):
                if text[0:6] == '開始對話模式':
                    reply_message("對話模式已開始", tk, access_token)
                elif text[0:6] == '結束對話模式':
                    firestore.update_firestore_field('Linebot_'+client+'ID',ID,'IsTalking',False)
                    firestore.delete_firestore_field('Linebot_'+client+'ID',ID,'messages')
                    reply_message("對話模式已結束", tk, access_token)
                elif text[0:6] == '清空對話紀錄':
                    firestore.delete_firestore_field('Linebot_'+client+'ID',ID,'messages')
                    reply_message("對話紀錄已清空", tk, access_token)
                else:
                    reply_message(chatmode(text,client,ID), tk, access_token)
            elif firestore.get_firestore_field('Linebot_'+client+'ID',ID,'IsAccountingName'):
                if firestore.get_firestore_field('Linebot_'+client+'ID',ID,'IsAccountingType'):
                    try:
                        typ = int(text)
                        if typ not in [1,2,3,4,5,6,7,8,11]:
                            raise
                        ammount = firestore.get_firestore_field('Linebot_'+client+'ID',ID,'AccountingTmpAmmount')
                        name = firestore.get_firestore_field('Linebot_'+client+'ID',ID,'AccountingTmpName')
                        tz = timezone(timedelta(hours=+8))
                        today = datetime.now(tz)
                        date = today.strftime("%Y_%m_%d")
                        firestore.append_firestore_array_field('Linebot_'+client+'ID',ID,'Accounts_'+date[:7],[{"Name": name, "Ammount": ammount, "Type": typ, "Date": date}])
                        firestore.delete_firestore_field('Linebot_'+client+'ID',ID,'AccountingTmpName')
                        firestore.delete_firestore_field('Linebot_'+client+'ID',ID,'AccountingTmpAmmount')
                        firestore.update_firestore_field('Linebot_'+client+'ID',ID,'IsAccountingType',False)
                        firestore.update_firestore_field('Linebot_'+client+'ID',ID,'IsAccountingAmmount',False)
                        firestore.update_firestore_field('Linebot_'+client+'ID',ID,'IsAccountingName',False)
                        reply_message(f'項目名稱:{name} 金額:{ammount} 類別:{typ} 輸入成功', tk, access_token)
                    except:
                        reply_message("格式錯誤，請輸入類別代號\n1飲食 2生活 3居住 4交通 5娛樂 6醫療 7其他 8投資 11收入", tk, access_token)
                else:
                    if firestore.get_firestore_field('Linebot_'+client+'ID',ID,'IsAccountingAmmount'):
                        try:
                            ammount = float(text)
                            firestore.update_firestore_field('Linebot_'+client+'ID',ID,'AccountingTmpAmmount',ammount)
                            firestore.update_firestore_field('Linebot_'+client+'ID',ID,'IsAccountingType',True)
                            reply_message("請輸入類別代號\n1飲食 2生活 3居住 4交通 5娛樂 6醫療 7其他 8投資 11收入", tk, access_token)
                        except:
                            reply_message("格式錯誤，請輸入金額數字", tk, access_token)
                    else:
                        firestore.update_firestore_field('Linebot_'+client+'ID',ID,'AccountingTmpName',text)
                        firestore.update_firestore_field('Linebot_'+client+'ID',ID,'IsAccountingAmmount',True)
                        reply_message("請輸入金額", tk, access_token)
            elif firestore.get_firestore_field('Linebot_'+client+'ID',ID,'IsHistory'):
                    try:
                        if len(text) != 6:
                            raise
                        if int(text[:4]) < 1900 or int(text[:4]) > 2399:
                            raise
                        if int(text[4:]) < 1 or int(text[4:]) > 12:
                            raise
                    except:
                        reply_message("格式錯誤，請輸入年月\nex.202307", tk, access_token)
                    summation = account_monthly(client, ID, text[:4]+"_"+text[4:])
                    percentages = pie_chart(["飲食","生活","居住","交通","娛樂","醫療","其他","投資"],summation[0],text[:4]+"年"+text[4:]+"月統計")
                    gcs.upload_blob("asia.artifacts.watermelon-368305.appspot.com", "./accounts-pie-chart.png", f'accounts-pie-chart/pie-chart{tk}.png')
                    gcs.make_blob_public("asia.artifacts.watermelon-368305.appspot.com", f'accounts-pie-chart/pie-chart{tk}.png')
                    image_url = f'https://storage.googleapis.com/asia.artifacts.watermelon-368305.appspot.com/accounts-pie-chart/pie-chart{tk}.png'
                    content = {"type":"carousel","contents":[{"type":"bubble","hero":{"type":"image","size":"full","aspectRatio":"20:18","aspectMode":"cover","url":image_url},"body":{"type":"box","layout":"vertical","spacing":"sm","contents":[{"type":"box","layout":"vertical","spacing":"sm","contents":[{"type":"text","text":"支出總計:"+str(sum(summation[0]))+"元","wrap":True,"weight":"bold","size":"lg","color": "#FF0000"}],"alignItems":"center"},{"type":"box","layout":"vertical","spacing":"sm","contents":[{"type":"text","text":"飲食:"+str(summation[0][0])+"元("+percentages[0]+")","wrap":True,"weight":"bold","size":"sm"}],"alignItems":"center"},{"type":"box","layout":"vertical","spacing":"sm","contents":[{"type":"text","text":"生活:"+str(summation[0][1])+"元("+percentages[1]+")","wrap":True,"weight":"bold","size":"sm"}],"alignItems":"center"},{"type":"box","layout":"vertical","spacing":"sm","contents":[{"type":"text","text":"居住:"+str(summation[0][2])+"元("+percentages[2]+")","wrap":True,"weight":"bold","size":"sm"}],"alignItems":"center"},{"type":"box","layout":"vertical","spacing":"sm","contents":[{"type":"text","text":"交通:"+str(summation[0][3])+"元("+percentages[3]+")","wrap":True,"weight":"bold","size":"sm"}],"alignItems":"center"},{"type":"box","layout":"vertical","spacing":"sm","contents":[{"type":"text","text":"娛樂:"+str(summation[0][4])+"元("+percentages[4]+")","wrap":True,"weight":"bold","size":"sm"}],"alignItems":"center"},{"type":"box","layout":"vertical","spacing":"sm","contents":[{"type":"text","text":"醫療:"+str(summation[0][5])+"元("+percentages[5]+")","wrap":True,"weight":"bold","size":"sm"}],"alignItems":"center"},{"type":"box","layout":"vertical","spacing":"sm","contents":[{"type":"text","text":"其他:"+str(summation[0][6])+"元("+percentages[6]+")","wrap":True,"weight":"bold","size":"sm"}],"alignItems":"center"},{"type":"box","layout":"vertical","spacing":"sm","contents":[{"type":"text","text":"投資:"+str(summation[0][7])+"元("+percentages[7]+")","wrap":True,"weight":"bold","size":"sm"}],"alignItems":"center"},{"type":"box","layout":"vertical","spacing":"sm","contents":[{"type":"text","text":"收入總計:"+str(summation[1])+"元","wrap":True,"weight":"bold","size":"lg","color": "#00FF00"}],"alignItems":"center"},{"type":"box","layout":"vertical","spacing":"sm","contents":[{"type":"text","text":"收支損益:"+str(summation[1]-sum(summation[0]))+"元","wrap":True,"weight":"bold","size":"lg"}],"alignItems":"center"}]}}]}
                    firestore.update_firestore_field('Linebot_'+client+'ID',ID,'IsHistory',False)
                    reply_flex_message(text, content, tk, access_token)
            elif firestore.get_firestore_field('Linebot_'+client+'ID',ID,'IsReport'):
                    try:
                        if len(text) != 6:
                            raise
                        if int(text[:4]) < 1900 or int(text[:4]) > 2399:
                            raise
                        if int(text[4:]) < 1 or int(text[4:]) > 12:
                            raise
                    except:
                        reply_message("格式錯誤，請輸入年月\nex.202307", tk, access_token)
                    data = firestore.get_firestore_field('Linebot_'+client+'ID',ID,'Accounts_'+text[:4]+"_"+text[4:])
                    headers = list(data[0].keys())
                    values =[]
                    for item in data:
                        values.append(list(item.values()))
                    gss.delete_worksheet_if_exist('1gDQm8KEvNmO5zlzKoCkCbIZ-7BGJUm9NU7aBKxGkn5k',text[:4]+"_"+text[4:])
                    gss.create_worksheet('1gDQm8KEvNmO5zlzKoCkCbIZ-7BGJUm9NU7aBKxGkn5k',text[:4]+"_"+text[4:])
                    gss.append_data('1gDQm8KEvNmO5zlzKoCkCbIZ-7BGJUm9NU7aBKxGkn5k',text[:4]+"_"+text[4:],[headers])
                    gss.append_data('1gDQm8KEvNmO5zlzKoCkCbIZ-7BGJUm9NU7aBKxGkn5k',text[:4]+"_"+text[4:],values)
                    if int(text[4:]) == 1:
                        old_table = str(int(text[:4])-1)+"_12"
                    elif int(text[4:]) in [11,12]:
                        text[:4]+"_"+str(int(text[4:])-1)
                    else:
                        old_table = text[:4]+"_0"+str(int(text[4:])-1)
                    update_table = [["","Type","Ammount","percetage","MoM"],
                    ["1","飲食",'=SUMIF($A$2:$A,"=1",$B$2:$B)',"=G2/$G$13",f'=G2-{old_table}!G2'],
                    ["2","生活",'=SUMIF($A$2:$A,"=2",$B$2:$B)',"=G3/$G$13",f'=G3-{old_table}!G3'],
                    ["3","居住",'=SUMIF($A$2:$A,"=3",$B$2:$B)',"=G4/$G$13",f'=G4-{old_table}!G4'],
                    ["4","交通",'=SUMIF($A$2:$A,"=4",$B$2:$B)',"=G5/$G$13",f'=G5-{old_table}!G5'],
                    ["5","娛樂",'=SUMIF($A$2:$A,"=5",$B$2:$B)',"=G6/$G$13",f'=G6-{old_table}!G6'],
                    ["6","醫療",'=SUMIF($A$2:$A,"=6",$B$2:$B)',"=G7/$G$13",f'=G7-{old_table}!G7'],
                    ["7","其他",'=SUMIF($A$2:$A,"=7",$B$2:$B)',"=G8/$G$13",f'=G8-{old_table}!G8'],
                    ["8","投資",'=SUMIF($A$2:$A,"=8",$B$2:$B)',"=G9/$G$13",f'=G9-{old_table}!G9'],
                    ["","","","",""],
                    ["","","","",""],
                    ["11","收入",'=SUMIF($A$2:$A,"=11",$B$2:$B)',"",f'=G12-{old_table}!G12'],
                    ["","支出","=SUM(G2:G9)","",f'=G13-{old_table}!G13'],
                    ["","損益","=G12-SUM(G2:G9)","",""]]
                    r = gss.update_table('1gDQm8KEvNmO5zlzKoCkCbIZ-7BGJUm9NU7aBKxGkn5k',text[:4]+"_"+text[4:],update_table,"E1")
                    gss.set_format_percent('1gDQm8KEvNmO5zlzKoCkCbIZ-7BGJUm9NU7aBKxGkn5k',text[:4]+"_"+text[4:],'H2:H9')
                    firestore.update_firestore_field('Linebot_'+client+'ID',ID,'IsReport',False)
                    reply_message("明細已匯出，前往:"+r, tk, access_token)
            else:
                if text == '雷達' or text == '雷達回波':
                    reply_image(f'https://cwbopendata.s3.ap-northeast-1.amazonaws.com/MSC/O-A0058-001.png?{time.time_ns()}', tk, access_token)
                elif text == '衛星雲圖':
                    reply_image(f'https://cwbopendata.s3.ap-northeast-1.amazonaws.com/MSC/O-C0042-002.jpg?{time.time_ns()}', tk, access_token)
                elif text == '颱風':
                    reply_image(f'https://cwbopendata.s3.ap-northeast-1.amazonaws.com/MSC/O-B0032-002.jpg?{time.time_ns()}', tk, access_token)
                elif text == '地震資訊' or text == '地震':
                    quake = earth_quake()                           # 爬取地震資訊
                    push_message(quake[0], ID, access_token)  # 傳送地震資訊 ( 用 push 方法，因為 reply 只能用一次 )
                    reply_image(quake[1], tk, access_token)         # 傳送地震圖片 ( 用 reply 方法 )
                elif text[0:2] == '畫，' or text[0:2] == '畫,':
                    openai_image_url = dalle(text[2:])
                    reply_image(openai_image_url, tk, access_token)
                elif text[0:2] == '聊，' or text[0:2] == '聊,':
                    completion = openai.ChatCompletion.create(model="gpt-4", messages=[{"role": "user", "content": text[2:]+"(請使用繁體中文回覆)"}])
                    reply_msg = completion.choices[0].message.content
                    reply_message(reply_msg, tk, access_token)
                elif text == '扛' or text == '坦':
                    reply_image(get_meme(), tk, access_token)
                elif text == '抽':
                    reply_image(get_beauty(), tk, access_token)
                elif text in ('牡羊','金牛','雙子','巨蟹','獅子','處女','天秤','天蠍','射手','魔羯','水瓶','雙魚'):
                    reply_message(get_luck(text), tk, access_token)
                elif text == '!help' or text == '！help':
                    reply_msg = f'指令說明\n扛 或 坦 - 打了你就知道啦~~\n抽 - 抽美女帥哥圖\n聊， - ChatGPT陪你聊天\n畫， - DALL-E合成圖片\n星座 例如:處女  - 回報運勢\n語音訊息 - 語音翻譯機翻成繁體中文\n加密貨幣:<交易對id> - 顯示價格\n!氣象 - 氣象指令說明\n!新聞 - 新聞指令說明\n!對話模式 - 對話模式指令說明'
                    reply_message(reply_msg , tk, access_token)
                #elif text == '加密貨幣:列表' or text == '加密貨幣：列表':
                #    reply_message(get_cryptocurrency_market(), tk, access_token)
                elif text == '!氣象' or text == '！氣象':
                    reply_msg = f'氣象指令說明\n地震 - 傳送最近一筆地震資訊\n雷達回波 - 傳送雷達回波圖\n衛星雲圖 - 傳送衛星雲圖\n颱風 - 傳送東亞衛星雲圖\n發送位置 - 回報天氣資訊和預報'
                    reply_message(reply_msg , tk, access_token)
                elif text == '!記帳' or text == '！記帳':
                    reply_msg = f'記帳指令說明\n記帳 - 紀錄新項目\n月帳 - 當月統計\n歷史 - 歷史月帳'
                    reply_message(reply_msg , tk, access_token)
                elif text == '!新聞' or text == '！新聞':
                    reply_msg = f'新聞指令說明\n焦點新聞 - 三則焦點新聞\n國際新聞 - 三則國際新聞\n商業新聞 - 三則商業新聞\n科技新聞 - 三則科技新聞\n體育新聞 - 三則體育新聞\n娛樂新聞 - 三則娛樂新聞'
                    reply_message(reply_msg , tk, access_token)
                elif text == '!對話模式' or text == '！對話模式':
                    reply_msg = f'對話模式指令說明\n開始對話模式 - 開始ChatGPT對話模式\n結束對話模式 - 結束ChatGPT對話模式\n清空對話紀錄 - 在對話模式過程中使用此指令，可讓ChatGPT遺忘先前的對話紀錄'
                    reply_message(reply_msg , tk, access_token)
                elif text[0:5] == '加密貨幣:' or text == '加密貨幣：':
                    reply_message(cryptocurrency(text[5:]), tk, access_token)
                elif text[0:6] == '開始對話模式':
                    firestore.update_firestore_field('Linebot_'+client+'ID',ID,'IsTalking',True)
                    firestore.delete_firestore_field('Linebot_'+client+'ID',ID,'messages')
                    reply_message('對話模式已開始', tk, access_token)
                elif text in ["焦點新聞","國際新聞","商業新聞","科技新聞","體育新聞","娛樂新聞"]:
                    if text == "焦點新聞":
                        content = news("焦點新聞")
                    elif text == "國際新聞":
                        content = news("國際新聞")
                    elif text == "商業新聞":
                        content = news("商業新聞")
                    elif text == "科技新聞":
                        content = news("科技新聞")
                    elif text == "體育新聞":
                        content = news("體育新聞")
                    elif text == "娛樂新聞":
                        content = news("娛樂新聞")
                    reply_flex_message(text, content, tk, access_token)
                elif text == "記帳":
                    firestore.update_firestore_field('Linebot_'+client+'ID',ID,'IsAccountingName',True)
                    reply_message('請輸入項目名稱', tk, access_token)
                elif text == "月帳":
                    summation = account_monthly(client, ID, datetime.now(timezone(timedelta(hours=+8))).strftime("%Y_%m_%d"))
                    percentages = pie_chart(["飲食","生活","居住","交通","娛樂","醫療","其他","投資"],summation[0],"本月統計")
                    gcs.upload_blob("asia.artifacts.watermelon-368305.appspot.com", "./accounts-pie-chart.png", f'accounts-pie-chart/pie-chart{tk}.png')
                    gcs.make_blob_public("asia.artifacts.watermelon-368305.appspot.com", f'accounts-pie-chart/pie-chart{tk}.png')
                    image_url = f'https://storage.googleapis.com/asia.artifacts.watermelon-368305.appspot.com/accounts-pie-chart/pie-chart{tk}.png'
                    content = {"type":"carousel","contents":[{"type":"bubble","hero":{"type":"image","size":"full","aspectRatio":"20:18","aspectMode":"cover","url":image_url},"body":{"type":"box","layout":"vertical","spacing":"sm","contents":[{"type":"box","layout":"vertical","spacing":"sm","contents":[{"type":"text","text":"支出總計:"+str(sum(summation[0]))+"元","wrap":True,"weight":"bold","size":"lg","color": "#FF0000"}],"alignItems":"center"},{"type":"box","layout":"vertical","spacing":"sm","contents":[{"type":"text","text":"飲食:"+str(summation[0][0])+"元("+percentages[0]+")","wrap":True,"weight":"bold","size":"sm"}],"alignItems":"center"},{"type":"box","layout":"vertical","spacing":"sm","contents":[{"type":"text","text":"生活:"+str(summation[0][1])+"元("+percentages[1]+")","wrap":True,"weight":"bold","size":"sm"}],"alignItems":"center"},{"type":"box","layout":"vertical","spacing":"sm","contents":[{"type":"text","text":"居住:"+str(summation[0][2])+"元("+percentages[2]+")","wrap":True,"weight":"bold","size":"sm"}],"alignItems":"center"},{"type":"box","layout":"vertical","spacing":"sm","contents":[{"type":"text","text":"交通:"+str(summation[0][3])+"元("+percentages[3]+")","wrap":True,"weight":"bold","size":"sm"}],"alignItems":"center"},{"type":"box","layout":"vertical","spacing":"sm","contents":[{"type":"text","text":"娛樂:"+str(summation[0][4])+"元("+percentages[4]+")","wrap":True,"weight":"bold","size":"sm"}],"alignItems":"center"},{"type":"box","layout":"vertical","spacing":"sm","contents":[{"type":"text","text":"醫療:"+str(summation[0][5])+"元("+percentages[5]+")","wrap":True,"weight":"bold","size":"sm"}],"alignItems":"center"},{"type":"box","layout":"vertical","spacing":"sm","contents":[{"type":"text","text":"其他:"+str(summation[0][6])+"元("+percentages[6]+")","wrap":True,"weight":"bold","size":"sm"}],"alignItems":"center"},{"type":"box","layout":"vertical","spacing":"sm","contents":[{"type":"text","text":"投資:"+str(summation[0][7])+"元("+percentages[7]+")","wrap":True,"weight":"bold","size":"sm"}],"alignItems":"center"},{"type":"box","layout":"vertical","spacing":"sm","contents":[{"type":"text","text":"收入總計:"+str(summation[1])+"元","wrap":True,"weight":"bold","size":"lg","color": "#00FF00"}],"alignItems":"center"},{"type":"box","layout":"vertical","spacing":"sm","contents":[{"type":"text","text":"收支損益:"+str(summation[1]-sum(summation[0]))+"元","wrap":True,"weight":"bold","size":"lg"}],"alignItems":"center"}]}}]}
                    reply_flex_message(text, content, tk, access_token)
                elif text == "歷史":
                    firestore.update_firestore_field('Linebot_'+client+'ID',ID,'IsHistory',True)
                    reply_message('請輸入年月\nex.202307', tk, access_token)
                elif text == "明細":
                    firestore.update_firestore_field('Linebot_'+client+'ID',ID,'IsReport',True)
                    reply_message('請輸入年月\nex.202307', tk, access_token)
                else:
                    pass
        if type=='audio':
            completion = openai.ChatCompletion.create(model="gpt-4", messages=[{"role": "user", "content": "請將以下文字翻譯成繁體中文。\n"+speech_to_text(json_data['events'][0]['message']['id'])}])
            msg = completion.choices[0].message.content
            push_message(msg, ID, access_token)
            text_to_speech("cmn-TW-Wavenet-C",msg)
            gcs.upload_blob("asia.artifacts.watermelon-368305.appspot.com", "./text-to-speech.wav", f'text-to-speech/text-to-speech{tk}.wav')
            gcs.make_blob_public("asia.artifacts.watermelon-368305.appspot.com", f'text-to-speech/text-to-speech{tk}.wav')
            reply_audio(f'https://storage.googleapis.com/asia.artifacts.watermelon-368305.appspot.com/text-to-speech/text-to-speech{tk}.wav', tk, access_token)
        if type=='sticker':
            logger.info('sticker')
        if type=='video':
            logger.info('video')
    except Exception as e:
        logger.warning('exception'+e)                             # 如果發生錯誤，印出error
    return 'OK'                                                 # 驗證 Webhook 使用，不能省略

if __name__ == "__main__":
    app.run(host='0.0.0.0')