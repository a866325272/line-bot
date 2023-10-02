import requests, json, logging
logger = logging.getLogger('')

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

# LINE 回傳影片函式
def reply_video(preview, video, rk, token):
    headers = {'Authorization':f'Bearer {token}','Content-Type':'application/json'}
    body = {
    'replyToken':rk,
    'messages':[{
          'type': 'video',
          'originalContentUrl': video,
          'previewImageUrl': preview
        }]
    }
    req = requests.request('POST', 'https://api.line.me/v2/bot/message/reply', headers=headers,data=json.dumps(body).encode('utf-8'))
    logger.info("reply_img:"+video)

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

# LINE 回傳訊息複數函式
def reply_multi_message(msg, rk, token):
    headers = {'Authorization':f'Bearer {token}','Content-Type':'application/json'}
    body = {
    'replyToken':rk,
    'messages':msg
        # the below is message example in various type
        #{"type": "text","text": msg}
        #{'type': 'audio','originalContentUrl': msg,'duration': '600000'}
        #{'type': 'video','originalContentUrl': video,'previewImageUrl': preview}
        #{'type': 'image','originalContentUrl': msg,'previewImageUrl': msg}
    }
    req = requests.request('POST', 'https://api.line.me/v2/bot/message/reply', headers=headers,data=json.dumps(body).encode('utf-8'))
    logger.info("reply_multi_msg:"+str(msg))

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
