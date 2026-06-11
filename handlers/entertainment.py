"""娛樂功能: 表特圖、迷因圖、食物圖、星座運勢"""

import random
import requests
from random import choice
from bs4 import BeautifulSoup


def get_beauty() -> str:
    """取得表特圖"""
    url = 'https://jeff-dev.tplinkdns.com/beauty/'
    web = requests.get(url)
    soup = BeautifulSoup(web.text, "html.parser")
    links = soup.find('pre').find_all('a')
    link_values = [link.get('href') for link in links]
    random_link = random.choice(link_values)
    return url + random_link


def get_meme() -> str:
    """取得迷因圖"""
    imgs = []
    n = random.randrange(1, 76)
    url = 'https://memes.tw/wtf/user/125281?page=' + str(n)
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'}
    web = requests.get(url, headers=headers)
    soup = BeautifulSoup(web.text, "html.parser")
    links = soup.find_all("img", class_="img-fluid lazy")
    for link in links:
        if 'data-src' in link.attrs:
            imgs.append(link['data-src'])
    return choice(imgs)


def get_food() -> str:
    """取得食物圖"""
    url = 'https://jeff-dev.tplinkdns.com/food/'
    web = requests.get(url)
    soup = BeautifulSoup(web.text, "html.parser")
    links = soup.find('pre').find_all('a')
    link_values = [link.get('href') for link in links]
    random_link = random.choice(link_values)
    return url + random_link


def get_luck(sign: str) -> str:
    """取得今日星座運勢"""
    json_zodiac = {
        "牡羊": "0", "金牛": "1", "雙子": "2", "巨蟹": "3",
        "獅子": "4", "處女": "5", "天秤": "6", "天蠍": "7",
        "射手": "8", "魔羯": "9", "水瓶": "10", "雙魚": "11",
    }
    url = "https://astro.click108.com.tw/daily.php?iAstro=" + json_zodiac[sign]
    web = requests.get(url)
    soup = BeautifulSoup(web.text, "html.parser")
    luck = soup.find_all("div", class_="TODAY_CONTENT")
    luck_msg = str(luck).replace('[<div class="TODAY_CONTENT">', "")
    for tag in ['<h3>', '</h3>', '<p><span class="txt_green">', '<p><span class="txt_pink">',
                '<p><span class="txt_blue">', '<p><span class="txt_orange">',
                '</span></p><p>', '</p>', '</div>]']:
        luck_msg = luck_msg.replace(tag, "")
    luck_msg = luck_msg.replace(f"\n今", "今")
    luck_msg = luck_msg[0:len(luck_msg) - 1]
    return luck_msg
