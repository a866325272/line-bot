"""氣象相關: 目前天氣、天氣預報、空氣品質、地震、颱風"""

import io
import os
import time
import requests
import numpy
import statistics
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

from config import (
    CWA_TOKEN, EPA_TOKEN, ACCESS_TOKEN, SCREENSHOT_SERVICE_URL,
    logger, exception_handler,
)
import gcs
import lma


def aqi(address):
    """空氣品質"""
    city_list = {}
    msg = '找不到空氣品質資訊。'
    try:
        url = f'https://data.moenv.gov.tw/api/v2/aqx_p_432?api_key={EPA_TOKEN}&limit=1000&sort=ImportDate%20desc&format=JSON'
        a_data = requests.get(url)
        a_data_json = a_data.json()
        for i in a_data_json['records']:
            city = i['county']
            if city not in city_list:
                city_list[city] = []
            if i['aqi'] != '':
                aqi_val = int(i['aqi'])
                city_list[city].append(aqi_val)
        for i in city_list:
            if i in address:
                aqi_val = round(statistics.mean(city_list[i]), 0)
                if aqi_val <= 50:
                    aqi_status = '良好'
                elif aqi_val <= 100:
                    aqi_status = '普通'
                elif aqi_val <= 150:
                    aqi_status = '對敏感族群不健康'
                elif aqi_val <= 200:
                    aqi_status = '對所有族群不健康'
                elif aqi_val <= 300:
                    aqi_status = '非常不健康'
                else:
                    aqi_status = '危害'
                msg = i + f'空氣品質 :\n{aqi_status} ( AQI {aqi_val} )。'
                break
        return msg
    except:
        return msg


def radar_image_url():
    """取得最新雷達回波圖 URL（單張）"""
    return f'https://cwaopendata.s3.ap-northeast-1.amazonaws.com/Observation/O-A0058-001.png?{time.time_ns()}'


def radar_video(tk: str):
    """拉取最近 6 小時的雷達回波圖，合成 mp4 影片，回傳預覽圖 + Flex Video。

    氣象署每 10 分鐘產出一張雷達回波圖，6 小時 = 36 張。
    URL 格式: https://www.cwa.gov.tw/Data/radar/CV1_TW_3600_{YYYYMMDDHHMM}.png
    """
    import imageio.v3 as iio
    from PIL import Image

    try:
        tz = timezone(timedelta(hours=8))
        now = datetime.now(tz)
        minute = (now.minute // 10) * 10
        latest = now.replace(minute=minute, second=0, microsecond=0)

        # 往回取 6 小時 (36 張)，從舊到新排列
        timestamps = []
        for i in range(36, 0, -1):
            t = latest - timedelta(minutes=i * 10)
            timestamps.append(t)

        # 並行下載所有圖片
        session = requests.Session()
        session.verify = False

        def _download(t):
            ts_str = t.strftime('%Y%m%d%H%M')
            url = f'https://www.cwa.gov.tw/Data/radar/CV1_TW_3600_{ts_str}.png'
            try:
                resp = session.get(url, timeout=15)
                if resp.status_code == 200:
                    return (t, resp.content)
                else:
                    logger.warning(f'radar_gif: skip {ts_str}, status={resp.status_code}')
            except Exception as e:
                logger.warning(f'radar_gif: failed to download {ts_str}: {e}')
            return (t, None)

        with ThreadPoolExecutor(max_workers=6) as executor:
            results = list(executor.map(_download, timestamps))

        # resize 並轉成 numpy array
        frames = []
        last_full_content = None
        for t, content in results:
            if content:
                img = Image.open(io.BytesIO(content))
                img = img.resize((768, 768), Image.LANCZOS).convert('RGB')
                frames.append(numpy.array(img))
                last_full_content = content

        if not frames:
            lma.reply_message('無法取得雷達回波圖資料。', tk, ACCESS_TOKEN)
            return

        # 合成 mp4（fps=6，36 張約 6 秒 + 最後停頓）
        os.makedirs('videos', exist_ok=True)
        mp4_filename = f'radar_{tk}.mp4'
        local_path = f'videos/{mp4_filename}'

        # 最後一張多重複 4 幀讓觀看者看清最新狀態
        frames_with_pause = frames + [frames[-1]] * 4
        iio.imwrite(local_path, frames_with_pause, fps=6, codec='libx264')

        # 最新一張的 1024x1024 預覽圖
        preview_filename = f'radar_{tk}_preview.jpg'
        preview_path = f'videos/{preview_filename}'
        preview_img = Image.open(io.BytesIO(last_full_content))
        preview_img = preview_img.resize((1024, 1024), Image.LANCZOS).convert('RGB')
        preview_img.save(preview_path, format='JPEG', quality=85)

        # 上傳 GCS
        bucket = "asia.artifacts.watermelon-368305.appspot.com"
        gcs_video_path = f'radar/{mp4_filename}'
        gcs_preview_path = f'radar/{preview_filename}'

        gcs.upload_blob(bucket, local_path, gcs_video_path)
        gcs.make_blob_public(bucket, gcs_video_path)
        gcs.upload_blob(bucket, preview_path, gcs_preview_path)
        gcs.make_blob_public(bucket, gcs_preview_path)

        video_url = f'https://storage.googleapis.com/{bucket}/{gcs_video_path}'
        preview_url = f'https://storage.googleapis.com/{bucket}/{gcs_preview_path}'

        # 回傳：靜態預覽圖 + Flex Video
        time_range = f"{timestamps[0].strftime('%H:%M')} ~ {timestamps[-1].strftime('%H:%M')}"
        flex_content = {
            "type": "bubble",
            "size": "mega",
            "hero": {
                "type": "video",
                "url": video_url,
                "previewUrl": preview_url,
                "altContent": {
                    "type": "image",
                    "size": "full",
                    "aspectRatio": "1:1",
                    "aspectMode": "cover",
                    "url": preview_url,
                },
                "aspectRatio": "1:1",
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "paddingAll": "8px",
                "contents": [
                    {
                        "type": "text",
                        "text": "雷達回波動態圖（近 6 小時）",
                        "weight": "bold",
                        "size": "sm",
                    },
                    {
                        "type": "text",
                        "text": time_range,
                        "size": "xs",
                        "color": "#888888",
                    },
                ],
            },
        }

        reply_msg = (
            {
                "type": "image",
                "originalContentUrl": preview_url,
                "previewImageUrl": preview_url,
            },
            {
                "type": "flex",
                "altText": f"雷達回波動態圖 {time_range}",
                "contents": flex_content,
            },
        )
        lma.reply_multi_message(reply_msg, tk, ACCESS_TOKEN)

        # 清理本地檔案
        for f in (local_path, preview_path):
            try:
                os.remove(f)
            except OSError:
                pass

    except Exception as e:
        exception_handler(e)
        lma.reply_message('雷達回波動態圖產生失敗，請稍後再試。', tk, ACCESS_TOKEN)


def satellite_video(tk: str):
    """拉取最近 6 小時的衛星雲圖，合成 mp4 影片，回傳預覽圖 + Flex Video。

    氣象署每 10 分鐘產出一張衛星雲圖，6 小時 = 36 張。
    URL 格式: https://www.cwa.gov.tw/Data/satellite/TWI_IR1_CR_800/TWI_IR1_CR_800-{YYYY}-{MM}-{DD}-{HH}-{mm}.jpg
    """
    import imageio.v3 as iio
    from PIL import Image

    try:
        tz = timezone(timedelta(hours=8))
        now = datetime.now(tz)
        minute = (now.minute // 10) * 10
        latest = now.replace(minute=minute, second=0, microsecond=0)

        # 往回取 6 小時 (36 張)，從舊到新排列
        timestamps = []
        for i in range(36, 0, -1):
            t = latest - timedelta(minutes=i * 10)
            timestamps.append(t)

        # 並行下載所有圖片
        session = requests.Session()
        session.verify = False

        def _download(t):
            ts_str = t.strftime('%Y-%m-%d-%H-%M')
            url = f'https://www.cwa.gov.tw/Data/satellite/TWI_IR1_CR_800/TWI_IR1_CR_800-{ts_str}.jpg'
            try:
                resp = session.get(url, timeout=15)
                if resp.status_code == 200:
                    return (t, resp.content)
                else:
                    logger.warning(f'satellite_video: skip {ts_str}, status={resp.status_code}')
            except Exception as e:
                logger.warning(f'satellite_video: failed to download {ts_str}: {e}')
            return (t, None)

        with ThreadPoolExecutor(max_workers=6) as executor:
            results = list(executor.map(_download, timestamps))

        # resize 並轉成 numpy array
        frames = []
        last_full_content = None
        for t, content in results:
            if content:
                img = Image.open(io.BytesIO(content))
                img = img.resize((768, 768), Image.LANCZOS).convert('RGB')
                frames.append(numpy.array(img))
                last_full_content = content

        if not frames:
            lma.reply_message('無法取得衛星雲圖資料。', tk, ACCESS_TOKEN)
            return

        # 合成 mp4（fps=6，36 張約 6 秒 + 最後停頓）
        os.makedirs('videos', exist_ok=True)
        mp4_filename = f'satellite_{tk}.mp4'
        local_path = f'videos/{mp4_filename}'

        # 最後一張多重複 4 幀讓觀看者看清最新狀態
        frames_with_pause = frames + [frames[-1]] * 4
        iio.imwrite(local_path, frames_with_pause, fps=6, codec='libx264')

        # 最新一張的 1024x1024 預覽圖
        preview_filename = f'satellite_{tk}_preview.jpg'
        preview_path = f'videos/{preview_filename}'
        preview_img = Image.open(io.BytesIO(last_full_content))
        preview_img = preview_img.resize((1024, 1024), Image.LANCZOS).convert('RGB')
        preview_img.save(preview_path, format='JPEG', quality=85)

        # 上傳 GCS
        bucket = "asia.artifacts.watermelon-368305.appspot.com"
        gcs_video_path = f'satellite/{mp4_filename}'
        gcs_preview_path = f'satellite/{preview_filename}'

        gcs.upload_blob(bucket, local_path, gcs_video_path)
        gcs.make_blob_public(bucket, gcs_video_path)
        gcs.upload_blob(bucket, preview_path, gcs_preview_path)
        gcs.make_blob_public(bucket, gcs_preview_path)

        video_url = f'https://storage.googleapis.com/{bucket}/{gcs_video_path}'
        preview_url = f'https://storage.googleapis.com/{bucket}/{gcs_preview_path}'

        # 回傳：靜態預覽圖 + Flex Video
        time_range = f"{timestamps[0].strftime('%H:%M')} ~ {timestamps[-1].strftime('%H:%M')}"
        flex_content = {
            "type": "bubble",
            "size": "mega",
            "hero": {
                "type": "video",
                "url": video_url,
                "previewUrl": preview_url,
                "altContent": {
                    "type": "image",
                    "size": "full",
                    "aspectRatio": "1:1",
                    "aspectMode": "cover",
                    "url": preview_url,
                },
                "aspectRatio": "1:1",
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "paddingAll": "8px",
                "contents": [
                    {
                        "type": "text",
                        "text": "衛星雲圖動態圖（近 6 小時）",
                        "weight": "bold",
                        "size": "sm",
                    },
                    {
                        "type": "text",
                        "text": time_range,
                        "size": "xs",
                        "color": "#888888",
                    },
                ],
            },
        }

        reply_msg = (
            {
                "type": "image",
                "originalContentUrl": preview_url,
                "previewImageUrl": preview_url,
            },
            {
                "type": "flex",
                "altText": f"衛星雲圖動態圖 {time_range}",
                "contents": flex_content,
            },
        )
        lma.reply_multi_message(reply_msg, tk, ACCESS_TOKEN)

        # 清理本地檔案
        for f in (local_path, preview_path):
            try:
                os.remove(f)
            except OSError:
                pass

    except Exception as e:
        exception_handler(e)
        lma.reply_message('衛星雲圖動態圖產生失敗，請稍後再試。', tk, ACCESS_TOKEN)


def forecast(address):
    """氣象預報"""
    area_list = {}
    json_api = {
        "宜蘭縣": "F-D0047-003", "桃園市": "F-D0047-007", "新竹縣": "F-D0047-011",
        "苗栗縣": "F-D0047-015", "彰化縣": "F-D0047-019", "南投縣": "F-D0047-023",
        "雲林縣": "F-D0047-027", "嘉義縣": "F-D0047-031", "屏東縣": "F-D0047-035",
        "臺東縣": "F-D0047-039", "花蓮縣": "F-D0047-043", "澎湖縣": "F-D0047-047",
        "基隆市": "F-D0047-051", "新竹市": "F-D0047-055", "嘉義市": "F-D0047-059",
        "臺北市": "F-D0047-063", "高雄市": "F-D0047-067", "新北市": "F-D0047-071",
        "臺中市": "F-D0047-075", "臺南市": "F-D0047-079", "連江縣": "F-D0047-083",
        "金門縣": "F-D0047-087",
    }
    msg = '找不到天氣預報資訊。'
    try:
        url = f'https://opendata.cwa.gov.tw/fileapi/v1/opendataapi/F-C0032-001?Authorization={CWA_TOKEN}&downloadType=WEB&format=JSON'
        f_data = requests.get(url)
        f_data_json = f_data.json()
        location = f_data_json['cwaopendata']['dataset']['location']
        for i in location:
            city = i['locationName']
            area_list[city] = ''
        for i in area_list:
            if i in address:
                msg = area_list[i]
                url = f'https://opendata.cwa.gov.tw/api/v1/rest/datastore/{json_api[i]}?Authorization={CWA_TOKEN}&elementName=WeatherDescription'
                f_data = requests.get(url)
                f_data_json = f_data.json()
                location = f_data_json['records']['Locations'][0]['Location']
                city = i
                break
        for i in location:
            area = i['LocationName']
            starttime = i['WeatherElement'][-1]['Time'][0]['StartTime']
            endtime = i['WeatherElement'][-1]['Time'][0]['EndTime']
            starttime = starttime[5:10] + " " + starttime[11:16]
            endtime = endtime[5:10] + " " + endtime[11:16]
            wd = i['WeatherElement'][-1]['Time'][0]['ElementValue'][0]['WeatherDescription']
            starttime1 = i['WeatherElement'][-1]['Time'][1]['StartTime']
            endtime1 = i['WeatherElement'][-1]['Time'][1]['EndTime']
            starttime1 = starttime1[5:10] + " " + starttime1[11:16]
            endtime1 = endtime1[5:10] + " " + endtime1[11:16]
            wd1 = i['WeatherElement'][-1]['Time'][1]['ElementValue'][0]['WeatherDescription']
            if area in address:
                msg = city + area + f'天氣預報 :\n{starttime} ~ {endtime}\n{wd}\n\n{starttime1} ~ {endtime1}\n{wd1}'
                break
        return msg
    except:
        return msg


def current_weather(address):
    """目前天氣"""
    city_list, city_list_avg, area_list, area_list2_avg = {}, {}, {}, {}
    msg = '找不到氣象資訊。'

    def get_data(url):
        w_data = requests.get(url)
        w_data_json = w_data.json()
        stations = w_data_json['cwaopendata']['dataset']['Station']
        for station in stations:
            city = station['GeoInfo']['CountyName']
            area = station['GeoInfo']['TownName']
            city_area = city + area
            weather = station['WeatherElement']['Weather']
            temp = _check_data(station['WeatherElement']['AirTemperature'])
            humd = _check_data(station['WeatherElement']['RelativeHumidity'])
            r24 = _check_data(station['WeatherElement']['Now']['Precipitation'])
            if city_area not in area_list:
                area_list[city_area] = {'temp': [], 'humd': [], 'r24': [], 'wx': []}
            if city not in city_list:
                city_list[city] = {'temp': [], 'humd': [], 'r24': [], 'wx': []}
            city_list[city]['temp'].append(temp)
            city_list[city]['humd'].append(humd)
            city_list[city]['r24'].append(r24)
            city_list[city]['wx'].append(weather)
            area_list[city_area]['temp'].append(temp)
            area_list[city_area]['humd'].append(humd)
            area_list[city_area]['r24'].append(r24)
            area_list[city_area]['wx'].append(weather)

    def _check_data(e):
        return numpy.nan if float(e) < 0 else float(e)

    def _msg_content(loc_list, msg):
        for loc in loc_list:
            if loc in address:
                temp = f"氣溫 {loc_list[loc]['temp']} 度，" if loc_list[loc]['temp'] is not None else ''
                humd = f"相對濕度 {loc_list[loc]['humd']}%，" if loc_list[loc]['humd'] is not None else ''
                r24 = f"累積雨量 {loc_list[loc]['r24']}mm，" if loc_list[loc]['r24'] is not None else ''
                wx = f"{loc_list[loc]['wx'][0]}，" if loc_list[loc]['r24'] is not None else ''
                description = loc + f'目前天氣 :\n{wx}{temp}{humd}{r24}'.strip('，')
                msg = f'{description}。'
                break
        return msg

    try:
        get_data(f'https://opendata.cwa.gov.tw/fileapi/v1/opendataapi/O-A0001-001?Authorization={CWA_TOKEN}&downloadType=WEB&format=JSON')
        get_data(f'https://opendata.cwa.gov.tw/fileapi/v1/opendataapi/O-A0003-001?Authorization={CWA_TOKEN}&downloadType=WEB&format=JSON')
        for city in city_list:
            if city not in city_list_avg:
                city_list_avg[city] = {
                    'temp': round(numpy.nanmean(city_list[city]['temp']), 1),
                    'humd': round(numpy.nanmean(city_list[city]['humd']), 1),
                    'r24': round(numpy.nanmean(city_list[city]['r24']), 1),
                    'wx': city_list[city]['wx'],
                }
        for area in area_list:
            if area not in area_list2_avg:
                area_list2_avg[area] = {
                    'temp': round(numpy.nanmean(area_list[area]['temp']), 1),
                    'humd': round(numpy.nanmean(area_list[area]['humd']), 1),
                    'r24': round(numpy.nanmean(area_list[area]['r24']), 1),
                    'wx': area_list[area]['wx'],
                }
        msg = _msg_content(city_list_avg, msg)
        msg = _msg_content(area_list2_avg, msg)
        return msg
    except Exception as e:
        exception_handler(e)
        return msg


def _create_snapshot_video(sites, framerate, duration, width, height, preview_frames=None, headers=None):
    """呼叫 screenshot-service 進行截圖錄影"""
    import os as _os
    site_list = [[name, url] for name, url in sites]
    payload = {
        'sites': site_list,
        'framerate': framerate,
        'duration': duration,
        'width': width,
        'height': height,
    }
    if headers:
        payload['headers'] = headers
    logger.info(f'Calling screenshot service: {SCREENSHOT_SERVICE_URL}/capture with sites={[s[0] for s in site_list]}')
    resp = requests.post(f'{SCREENSHOT_SERVICE_URL}/capture', json=payload, timeout=600)
    resp.raise_for_status()
    results = resp.json()['results']
    logger.info(f'Screenshot service returned: {results}')

    _os.makedirs('pics', exist_ok=True)
    _os.makedirs('videos', exist_ok=True)

    for item in results:
        name = item['name']
        video_resp = requests.get(f'{SCREENSHOT_SERVICE_URL}/download/video/{name}.mp4', timeout=60)
        with open(f'videos/{name}.mp4', 'wb') as f:
            f.write(video_resp.content)
        if preview_frames:
            for frame_num in preview_frames:
                frame_filename = f'{name}_{frame_num:03d}.png'
                img_resp = requests.get(f'{SCREENSHOT_SERVICE_URL}/download/image/{frame_filename}', timeout=60)
                if img_resp.status_code == 200:
                    with open(f'pics/{frame_filename}', 'wb') as f:
                        f.write(img_resp.content)


def typhoon(tk: str, ID: str):
    """颱風預測 — 從 screenshot-service 取預先截好的影片，秒回"""
    try:
        ncdr_url = 'https://watch.ncdr.nat.gov.tw/watch_tracks_pro'
        windy_url = 'https://www.windy.com/?24.939,121.542,5'

        # 從 screenshot-service 取最新的預錄影片
        latest_resp = requests.get(f'{SCREENSHOT_SERVICE_URL}/latest/typhoon', timeout=10)
        latest_resp.raise_for_status()
        latest = latest_resp.json()

        if not latest.get('available'):
            # 沒有預錄檔案，fallback 到即時截圖
            logger.info('typhoon: no pre-captured files, falling back to live capture')
            _typhoon_live_capture(tk, ID)
            return

        # 下載影片和預覽圖到本地，再上傳 GCS
        os.makedirs('videos', exist_ok=True)
        os.makedirs('pics', exist_ok=True)

        gcs_bucket = "asia.artifacts.watermelon-368305.appspot.com"
        media = {}  # key -> {'video_url': ..., 'img_url': ...}

        for key in ('ncdr', 'windy'):
            info = latest.get(key)
            if not info:
                continue

            video_filename = info['video']
            preview_filename = info.get('preview')

            # 下載影片
            video_resp = requests.get(
                f'{SCREENSHOT_SERVICE_URL}/typhoon/download/{video_filename}', timeout=60)
            if video_resp.status_code != 200:
                continue
            local_video = f'videos/{video_filename}'
            with open(local_video, 'wb') as f:
                f.write(video_resp.content)

            # 下載預覽圖
            local_preview = None
            if preview_filename:
                img_resp = requests.get(
                    f'{SCREENSHOT_SERVICE_URL}/typhoon/download/{preview_filename}', timeout=60)
                if img_resp.status_code == 200:
                    local_preview = f'pics/{preview_filename}'
                    with open(local_preview, 'wb') as f:
                        f.write(img_resp.content)

            # 上傳 GCS（帶時間戳，避免 CDN 快取）
            gcs_video_path = f'typhoon/{video_filename}'
            gcs.upload_blob(gcs_bucket, local_video, gcs_video_path)
            gcs.make_blob_public(gcs_bucket, gcs_video_path)

            video_url = f'https://storage.googleapis.com/{gcs_bucket}/{gcs_video_path}'
            img_url = video_url  # fallback

            if local_preview:
                gcs_preview_path = f'typhoon/{preview_filename}'
                gcs.upload_blob(gcs_bucket, local_preview, gcs_preview_path)
                gcs.make_blob_public(gcs_bucket, gcs_preview_path)
                img_url = f'https://storage.googleapis.com/{gcs_bucket}/{gcs_preview_path}'

            media[key] = {'video_url': video_url, 'img_url': img_url}

            # 清理本地
            for f in (local_video, local_preview):
                if f:
                    try:
                        os.remove(f)
                    except OSError:
                        pass

        if not media:
            lma.reply_message('颱風截圖取得失敗，請稍後再試。', tk, ACCESS_TOKEN)
            return

        def _video_bubble(title, subtitle, video_url, preview_url):
            return {
                "type": "bubble",
                "size": "mega",
                "hero": {
                    "type": "video",
                    "url": video_url,
                    "previewUrl": preview_url,
                    "altContent": {
                        "type": "image",
                        "size": "full",
                        "aspectRatio": "1:1",
                        "aspectMode": "cover",
                        "url": preview_url,
                    },
                    "aspectRatio": "1:1",
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "paddingAll": "8px",
                    "contents": [
                        {"type": "text", "text": title, "weight": "bold", "size": "sm"},
                        {"type": "text", "text": subtitle, "size": "xs", "color": "#888888"},
                    ],
                },
            }

        messages = [{"type": "text", "text": f"NCDR路徑預測: {ncdr_url}\nWindy風地圖: {windy_url}"}]

        if 'ncdr' in media:
            messages.append({
                "type": "flex",
                "altText": "颱風路徑預測 - NCDR",
                "contents": _video_bubble("NCDR 颱風路徑預測", ncdr_url,
                                          media['ncdr']['video_url'], media['ncdr']['img_url']),
            })
        if 'windy' in media:
            messages.append({
                "type": "flex",
                "altText": "颱風風場 - Windy",
                "contents": _video_bubble("Windy 風場地圖", windy_url,
                                          media['windy']['video_url'], media['windy']['img_url']),
            })

        lma.reply_multi_message(messages, tk, ACCESS_TOKEN)

    except Exception as e:
        exception_handler(e)
        lma.reply_message('颱風資訊取得失敗，請稍後再試。', tk, ACCESS_TOKEN)


def _typhoon_live_capture(tk: str, ID: str):
    """Fallback: 即時截圖（原本的邏輯）"""
    ncdr_url = 'https://watch.ncdr.nat.gov.tw/watch_tracks_pro'
    windy_url = 'https://www.windy.com/?24.939,121.542,5'

    t1 = threading.Thread(target=_create_snapshot_video, args=([('typhoon', ncdr_url)], 4, 30, 1138, 640), kwargs={'preview_frames': [18]})
    t2 = threading.Thread(target=_create_snapshot_video, args=([('windy', windy_url)], 4, 30, 1138, 640), kwargs={'preview_frames': [18]})
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    gcs_bucket = "asia.artifacts.watermelon-368305.appspot.com"
    gcs.upload_blob(gcs_bucket, "./videos/typhoon.mp4", f'typhoon/typhoon{tk}.mp4')
    gcs.upload_blob(gcs_bucket, "./pics/typhoon_018.png", f'typhoon/typhoon{tk}.png')
    gcs.upload_blob(gcs_bucket, "./videos/windy.mp4", f'typhoon/windy{tk}.mp4')
    gcs.upload_blob(gcs_bucket, "./pics/windy_018.png", f'typhoon/windy{tk}.png')
    gcs.make_blob_public(gcs_bucket, f'typhoon/typhoon{tk}.mp4')
    gcs.make_blob_public(gcs_bucket, f'typhoon/typhoon{tk}.png')
    gcs.make_blob_public(gcs_bucket, f'typhoon/windy{tk}.mp4')
    gcs.make_blob_public(gcs_bucket, f'typhoon/windy{tk}.png')
    ncdr_img = f'https://storage.googleapis.com/{gcs_bucket}/typhoon/typhoon{tk}.png'
    ncdr_video = f'https://storage.googleapis.com/{gcs_bucket}/typhoon/typhoon{tk}.mp4'
    windy_img = f'https://storage.googleapis.com/{gcs_bucket}/typhoon/windy{tk}.png'
    windy_video = f'https://storage.googleapis.com/{gcs_bucket}/typhoon/windy{tk}.mp4'

    def _video_bubble(title, subtitle, video_url, preview_url):
        return {
            "type": "bubble",
            "size": "mega",
            "hero": {
                "type": "video",
                "url": video_url,
                "previewUrl": preview_url,
                "altContent": {
                    "type": "image",
                    "size": "full",
                    "aspectRatio": "1:1",
                    "aspectMode": "cover",
                    "url": preview_url,
                },
                "aspectRatio": "1:1",
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "paddingAll": "8px",
                "contents": [
                    {"type": "text", "text": title, "weight": "bold", "size": "sm"},
                    {"type": "text", "text": subtitle, "size": "xs", "color": "#888888"},
                ],
            },
        }

    reply_msg = (
        {"type": "text", "text": f"NCDR路徑預測: {ncdr_url}\nWindy風地圖: {windy_url}"},
        {
            "type": "flex",
            "altText": "颱風路徑預測 - NCDR",
            "contents": _video_bubble("NCDR 颱風路徑預測", ncdr_url, ncdr_video, ncdr_img),
        },
        {
            "type": "flex",
            "altText": "颱風風場 - Windy",
            "contents": _video_bubble("Windy 風場地圖", windy_url, windy_video, windy_img),
        },
    )
    lma.reply_multi_message(reply_msg, tk, ACCESS_TOKEN)


def earthquake(tk: str):
    """地震資訊 — 使用 ExpTech API + CWA 氣象署 API + earthquake-service 即時資料"""
    try:
        EARTHQUAKE_SERVICE_URL = os.environ.get('EARTHQUAKE_SERVICE_URL', 'http://earthquake-service:5002')

        # --- 1. 查詢 earthquake-service 取得即時 EEW 和最新報告 ---
        eew_alert = None
        last_eew_alert = None
        last_eew_time = None
        exptech_reports = None
        try:
            latest_resp = requests.get(f"{EARTHQUAKE_SERVICE_URL}/latest", timeout=5)
            if latest_resp.status_code == 200:
                latest_data = latest_resp.json()
                if latest_data.get("has_eew") and latest_data.get("eew"):
                    eew_alert = latest_data["eew"]
                # 取得最後一筆速報（即使目前沒有即時 EEW）
                if latest_data.get("last_eew"):
                    last_eew_alert = latest_data["last_eew"]
                    last_eew_time = latest_data.get("last_eew_time")
        except Exception:
            logger.info("earthquake-service unavailable, falling back to direct API")

        # --- 2. 從 ExpTech API 取得最新地震報告清單（作為 fallback）---
        if not exptech_reports:
            EXPTECH_API_URLS = [
                "https://api.core-tnn1.exptech.dev",
                "https://api.core-tyo1.exptech.dev",
                "https://api.lb.exptech.dev",
            ]
            for base_url in EXPTECH_API_URLS:
                try:
                    resp = requests.get(f"{base_url}/api/v2/eq/report?limit=5", timeout=10)
                    if resp.status_code == 200:
                        exptech_reports = resp.json()
                        break
                except Exception:
                    continue

        # --- 3. 從 CWA 氣象署 API 取得地震報告（含圖片）---
        cwa_reports = []  # 合併後的 CWA 地震報告列表（按時間由新到舊）
        try:
            url_significant = f'https://opendata.cwa.gov.tw/api/v1/rest/datastore/E-A0016-001?Authorization={CWA_TOKEN}'
            url_minor = f'https://opendata.cwa.gov.tw/api/v1/rest/datastore/E-A0015-001?Authorization={CWA_TOKEN}'
            e_data = requests.get(url_significant, timeout=15)
            e_data_json = e_data.json()
            e_data2 = requests.get(url_minor, timeout=15)
            e_data_json2 = e_data2.json()
            eq_significant = e_data_json['records']['Earthquake']
            eq_minor = e_data_json2['records']['Earthquake']

            # 合併兩個來源，按時間由新到舊排序取前 5 筆
            all_cwa = eq_significant + eq_minor
            all_cwa.sort(key=lambda x: x['EarthquakeInfo']['OriginTime'], reverse=True)
            cwa_reports = all_cwa[:5]
        except Exception:
            logger.info("CWA API failed, skipping report image")

        # --- 4. 組合回覆訊息 ---
        # 如果有即時 EEW 速報，加上警報訊息；否則顯示最近一次速報
        if eew_alert:
            eew_info = eew_alert[0] if isinstance(eew_alert, list) and eew_alert else eew_alert
            if isinstance(eew_info, dict) and eew_info.get("eq"):
                eq_info = eew_info["eq"]
                eew_text = (
                    f"🚨 地震速報（EEW）正在發生！\n"
                    f"📍 震央: {eq_info.get('loc', '未知')}\n"
                    f"📏 預估規模: M{eq_info.get('mag', '?')}\n"
                    f"🕳️ 深度: {eq_info.get('depth', '?')} 公里\n"
                    f"⚡ 來源: {eew_info.get('author', 'unknown')}\n"
                    f"📡 即時監控：https://www.youtube.com/watch?v=KyT4qSK8lJo\n\n"
                    f"ℹ️ 速報為即時資訊，下方報告圖由氣象署發布，可能有數分鐘延遲"
                )
            else:
                eew_text = None
        elif last_eew_alert:
            # 沒有即時 EEW，但有最近一次速報記錄
            eew_info = last_eew_alert[0] if isinstance(last_eew_alert, list) and last_eew_alert else last_eew_alert
            if isinstance(eew_info, dict) and eew_info.get("eq"):
                eq_info = eew_info["eq"]
                time_label = f"\n🕐 速報時間: {last_eew_time}" if last_eew_time else ""
                eew_text = (
                    f"📋 最近一次地震速報（EEW）\n"
                    f"📍 震央: {eq_info.get('loc', '未知')}\n"
                    f"📏 預估規模: M{eq_info.get('mag', '?')}\n"
                    f"🕳️ 深度: {eq_info.get('depth', '?')} 公里\n"
                    f"⚡ 來源: {eew_info.get('author', 'unknown')}"
                    f"{time_label}\n"
                    f"📡 即時監控：https://www.youtube.com/watch?v=KyT4qSK8lJo\n\n"
                    f"ℹ️ 速報為即時資訊，下方報告圖由氣象署發布，可能有數分鐘延遲"
                )
            else:
                eew_text = None
        else:
            eew_text = None

        # 最近地震列表 — carousel 格式（每筆地震一張卡片，橫向捲動，含報告圖）
        bubbles = []
        if cwa_reports:
            for eq in cwa_reports[:5]:
                eq_info = eq['EarthquakeInfo']
                eq_loc = eq_info['Epicenter']['Location']
                eq_mag = eq_info['EarthquakeMagnitude']['MagnitudeValue']
                eq_dep = eq_info['FocalDepth']
                eq_origin = eq_info['OriginTime']  # "2026-06-14T11:15:04+08:00"
                eq_img = eq.get('ReportImageURI')
                date_str = eq_origin[5:10].replace('-', '/')
                time_str = eq_origin[11:16]
                mag_val = float(eq_mag)

                # 規模顏色分級
                if mag_val >= 5:
                    mag_color = "#D32F2F"
                elif mag_val >= 4:
                    mag_color = "#E64A19"
                elif mag_val >= 3:
                    mag_color = "#F57C00"
                else:
                    mag_color = "#757575"

                bubble = {
                    "type": "bubble",
                    "size": "giga",
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {"type": "text", "text": f"🕐 {date_str} {time_str}", "weight": "bold", "size": "sm", "color": "#333333"},
                            {"type": "text", "text": f"📍 {eq_loc}", "size": "xs", "wrap": True, "color": "#555555", "margin": "sm"},
                            {"type": "text", "text": f"📏 芮氏規模 {eq_mag}", "size": "xs", "color": mag_color, "margin": "sm"},
                            {"type": "text", "text": f"🕳️ 深度 {eq_dep} 公里", "size": "xs", "color": "#888888", "margin": "sm"},
                        ],
                        "paddingAll": "12px",
                        "spacing": "sm",
                    },
                }
                if eq_img:
                    bubble["hero"] = {
                        "type": "image",
                        "url": eq_img,
                        "size": "full",
                        "aspectRatio": "4:3",
                        "aspectMode": "fit",
                        "action": {"type": "uri", "uri": eq_img},
                    }
                bubbles.append(bubble)
        elif exptech_reports:
            # Fallback: CWA 失敗時用 ExpTech 資料（無圖）
            for eq in exptech_reports[:5]:
                eq_ts = datetime.fromtimestamp(eq['time'] / 1000, tz=timezone(timedelta(hours=8)))
                date_str = eq_ts.strftime('%m/%d')
                time_str = eq_ts.strftime('%H:%M')
                mag_val = eq['mag']
                if mag_val >= 5:
                    mag_color = "#D32F2F"
                elif mag_val >= 4:
                    mag_color = "#E64A19"
                elif mag_val >= 3:
                    mag_color = "#F57C00"
                else:
                    mag_color = "#757575"

                bubbles.append({
                    "type": "bubble",
                    "size": "micro",
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {"type": "text", "text": f"M {mag_val}", "weight": "bold", "size": "lg", "color": mag_color},
                            {"type": "text", "text": eq['loc'], "size": "xxs", "wrap": True, "weight": "bold", "color": "#333333", "margin": "sm"},
                            {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {"type": "text", "text": f"📅 {date_str}  🕐 {time_str}", "size": "xxs", "color": "#888888"},
                                    {"type": "text", "text": f"🕳️ 深度 {eq['depth']} km", "size": "xxs", "color": "#888888"},
                                ],
                                "margin": "md",
                                "spacing": "xs",
                            },
                        ],
                        "paddingAll": "12px",
                        "spacing": "sm",
                    },
                })

        if not bubbles:
            bubbles.append({
                "type": "bubble",
                "size": "micro",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": "暫無近期地震資料", "size": "sm", "color": "#888888", "wrap": True}
                    ],
                    "paddingAll": "14px",
                },
            })

        flex_contents = {"type": "carousel", "contents": bubbles}

        # 組合回覆
        messages = []
        if eew_text:
            messages.append({"type": "text", "text": eew_text})
        messages.append({
            "type": "flex",
            "altText": "近期地震一覽",
            "contents": flex_contents,
        })

        reply_msg = tuple(messages)
        lma.reply_multi_message(reply_msg, tk, ACCESS_TOKEN)
    except Exception as e:
        exception_handler(e)


def earthquake_yt(tk: str):
    """地震資訊（舊版）— 使用 YouTube 即時地震監控截圖影片"""
    try:
        earthquake_yturl = 'https://www.youtube.com/embed/KyT4qSK8lJo?autoplay=1&controls=0&rel=0&modestbranding=1'
        _create_snapshot_video(
            [('earthquake', earthquake_yturl)], 6, 10, 1280, 720,
            preview_frames=[24], headers={"Referer": "https://www.google.com/"}
        )

        gcs.upload_blob("asia.artifacts.watermelon-368305.appspot.com", "./videos/earthquake.mp4", f'earthquake/earthquake{tk}.mp4')
        gcs.upload_blob("asia.artifacts.watermelon-368305.appspot.com", "./pics/earthquake_024.png", f'earthquake/earthquake{tk}.png')
        gcs.make_blob_public("asia.artifacts.watermelon-368305.appspot.com", f'earthquake/earthquake{tk}.mp4')
        gcs.make_blob_public("asia.artifacts.watermelon-368305.appspot.com", f'earthquake/earthquake{tk}.png')

        url = f'https://opendata.cwa.gov.tw/api/v1/rest/datastore/E-A0016-001?Authorization={CWA_TOKEN}'
        url2 = f'https://opendata.cwa.gov.tw/api/v1/rest/datastore/E-A0015-001?Authorization={CWA_TOKEN}'
        e_data = requests.get(url)
        e_data_json = e_data.json()
        e_data2 = requests.get(url2)
        e_data_json2 = e_data2.json()
        eq = e_data_json['records']['Earthquake']
        eq2 = e_data_json2['records']['Earthquake']

        for i in eq:
            loc = i['EarthquakeInfo']['Epicenter']['Location']
            val = i['EarthquakeInfo']['EarthquakeMagnitude']['MagnitudeValue']
            dep = i['EarthquakeInfo']['FocalDepth']
            eq_time = i['EarthquakeInfo']['OriginTime']
            img = i['ReportImageURI']
            break
        for i in eq2:
            loc2 = i['EarthquakeInfo']['Epicenter']['Location']
            val2 = i['EarthquakeInfo']['EarthquakeMagnitude']['MagnitudeValue']
            dep2 = i['EarthquakeInfo']['FocalDepth']
            eq_time2 = i['EarthquakeInfo']['OriginTime']
            img2 = i['ReportImageURI']
            break

        if eq_time > eq_time2:
            msg_text = f'地震報告: {loc}，芮氏規模 {val} 級，深度 {dep} 公里，發生時間 {eq_time}。'
            report_img = img
        else:
            msg_text = f'地震報告: {loc2}，芮氏規模 {val2} 級，深度 {dep2} 公里，發生時間 {eq_time2}。'
            report_img = img2

        earthquake_img = f'https://storage.googleapis.com/asia.artifacts.watermelon-368305.appspot.com/earthquake/earthquake{tk}.png'
        earthquake_video = f'https://storage.googleapis.com/asia.artifacts.watermelon-368305.appspot.com/earthquake/earthquake{tk}.mp4'

        flex_video = {
            "type": "bubble",
            "size": "mega",
            "hero": {
                "type": "video",
                "url": earthquake_video,
                "previewUrl": earthquake_img,
                "altContent": {
                    "type": "image",
                    "size": "full",
                    "aspectRatio": "16:9",
                    "aspectMode": "cover",
                    "url": earthquake_img,
                },
                "aspectRatio": "16:9",
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "paddingAll": "8px",
                "contents": [
                    {"type": "text", "text": "地震即時監控", "weight": "bold", "size": "sm"},
                    {"type": "text", "text": "YouTube 即時地震監測畫面", "size": "xs", "color": "#888888"},
                ],
            },
        }

        reply_msg = (
            {"type": "text", "text": msg_text},
            {
                "type": "flex",
                "altText": "地震即時監控",
                "contents": flex_video,
            },
            {'type': 'image', 'originalContentUrl': report_img, 'previewImageUrl': report_img},
        )
        lma.reply_multi_message(reply_msg, tk, ACCESS_TOKEN)
    except Exception as e:
        exception_handler(e)
