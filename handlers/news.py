"""新聞爬蟲"""

import requests
from bs4 import BeautifulSoup

# 新聞分類對應 URL
_NEWS_URLS = {
    "焦點新聞": "https://news.google.com/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNRFZxYUdjU0JYcG9MVlJYR2dKVVZ5Z0FQAQ?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant",
    "國際新聞": "https://news.google.com/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNRGx1YlY4U0JYcG9MVlJYR2dKVVZ5Z0FQAQ?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant",
    "商業新聞": "https://news.google.com/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNRGx6TVdZU0JYcG9MVlJYR2dKVVZ5Z0FQAQ?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant",
    "科技新聞": "https://news.google.com/topics/CAAqLAgKIiZDQkFTRmdvSkwyMHZNR1ptZHpWbUVnVjZhQzFVVnhvQ1ZGY29BQVAB?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant",
    "體育新聞": "https://news.google.com/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNRFp1ZEdvU0JYcG9MVlJYR2dKVVZ5Z0FQAQ?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant",
    "娛樂新聞": "https://news.google.com/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNREpxYW5RU0JYcG9MVlJYR2dKVVZ5Z0FQAQ?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant",
}


def news(cat: str):
    """取得新聞 carousel flex message"""
    url = _NEWS_URLS[cat]
    web = requests.get(url)
    soup = BeautifulSoup(web.text, "html.parser")
    tags = soup.select(".IBr9hb a")

    links = []
    for i in range(0, 10, 2):
        news_url = "https://news.google.com/" + tags[i]['href'][2:]
        web = requests.get(news_url, allow_redirects=False)
        links.append(web.headers['Location'])

    # 縮網址 + 取得標題
    short_links = []
    titles = []
    for link in links:
        req = requests.get("https://tinyurl.com/api-create.php?url=" + link)
        short_links.append(req.text)

    for short_link in short_links:
        req = requests.get(short_link)
        title_start = req.text.find("<title>")
        title_end = req.text.find("</title>", title_start)
        title = req.text[title_start + 7:title_end].strip()
        titles.append(title)

    # 組合 carousel
    bubbles = []
    for i in range(min(5, len(titles))):
        bubbles.append({
            "type": "bubble", "size": "micro",
            "body": {"type": "box", "layout": "vertical", "spacing": "sm", "contents": [
                {"type": "text", "wrap": True, "weight": "bold", "size": "sm", "text": titles[i]}
            ]},
            "footer": {"type": "box", "layout": "vertical", "spacing": "sm", "contents": [
                {"type": "button", "style": "primary", "action": {"type": "uri", "label": "前往連結", "uri": short_links[i]}, "height": "sm"}
            ]}
        })

    return {"type": "carousel", "contents": bubbles}
