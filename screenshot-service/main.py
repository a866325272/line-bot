"""
Screenshot Service - 獨立的網頁截圖錄影微服務
接收 HTTP 請求，使用 Playwright 截圖並用 FFmpeg 合成影片，回傳影片檔案。

新增：颱風定期排程截圖 + /latest/typhoon 端點
"""
import os
import glob
import time
import threading
import logging
import logging.handlers
import subprocess
import shutil
from datetime import datetime, timedelta, timezone
from flask import Flask, request, jsonify, send_file
from playwright.sync_api import sync_playwright

app = Flask(__name__)

PICS_DIR = '/app/pics'
VIDEOS_DIR = '/app/videos'
TYPHOON_DIR = '/app/typhoon'  # 颱風定期截圖專用目錄
TYPHOON_RETENTION_HOURS = 24  # 保留最近 24 小時的檔案
TYPHOON_INTERVAL_MINUTES = 30  # 每 30 分鐘截一次

# 颱風截圖目標
TYPHOON_SITES = [
    ('typhoon_ncdr', 'https://watch.ncdr.nat.gov.tw/watch_tracks_pro'),
    ('typhoon_windy', 'https://www.windy.com/?24.939,121.542,5'),
]

# log config
logger = logging.getLogger('')
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
rotate_handler = logging.handlers.TimedRotatingFileHandler('/var/log/screenshot-service/screenshot-service.log', when="h", interval=1, backupCount=720)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
rotate_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
logger.addHandler(rotate_handler)
logger.addHandler(console_handler)

# --- 颱風定期截圖排程 ---

_typhoon_scheduler_enabled = True  # 可透過 API 開關


def _capture_site(output_name, url, framerate=12, duration=30, width=1138, height=640):
    """對單一網站進行截圖錄影，回傳影片路徑和預覽圖路徑"""
    tmp_pics = os.path.join(TYPHOON_DIR, 'tmp_pics')
    os.makedirs(tmp_pics, exist_ok=True)

    # 清理暫存
    for f in os.listdir(tmp_pics):
        if f.startswith(output_name):
            os.remove(os.path.join(tmp_pics, f))

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True,
                args=[
                    '--use-gl=swiftshader',
                    '--enable-webgl',
                    '--ignore-gpu-blocklist',
                    '--no-sandbox',
                ]
            )
            context = browser.new_context(
                viewport={'width': width, 'height': height},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                           'AppleWebKit/537.36 (KHTML, like Gecko) '
                           'Chrome/123.0.0.0 Safari/537.36',
            )
            page = context.new_page()
            page.goto(url, wait_until='load', timeout=60000)

            num_frames = framerate * duration
            frame_interval = 1.0 / framerate

            for frame_count in range(num_frames):
                page.screenshot(
                    path=f'{tmp_pics}/{output_name}_{frame_count:03d}.png'
                )
                time.sleep(frame_interval)

            context.close()
            browser.close()

        # 時間戳
        tz = timezone(timedelta(hours=8))
        ts = datetime.now(tz).strftime('%Y%m%d_%H%M')

        # FFmpeg 合成影片
        video_filename = f'{output_name}_{ts}.mp4'
        video_path = os.path.join(TYPHOON_DIR, video_filename)
        ffmpeg_command = [
            'ffmpeg', '-y',
            '-framerate', str(framerate),
            '-i', f'{tmp_pics}/{output_name}_%03d.png',
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            video_path
        ]
        subprocess.run(ffmpeg_command, capture_output=True)

        # 預覽圖：取第 4 秒的幀（framerate * 4）
        preview_frame = framerate * 4
        preview_src = f'{tmp_pics}/{output_name}_{preview_frame:03d}.png'
        preview_filename = f'{output_name}_{ts}.png'
        preview_path = os.path.join(TYPHOON_DIR, preview_filename)
        if os.path.exists(preview_src):
            shutil.copy2(preview_src, preview_path)

        # 清理暫存圖片
        for f in os.listdir(tmp_pics):
            if f.startswith(output_name):
                os.remove(os.path.join(tmp_pics, f))

        logger.info(f'Typhoon capture done: {video_filename}')
        return video_path, preview_path

    except Exception as e:
        logger.error(f'Typhoon capture failed for {output_name}: {e}')
        return None, None


def _cleanup_old_files():
    """清理超過 retention 時間的颱風檔案"""
    now = time.time()
    cutoff = now - (TYPHOON_RETENTION_HOURS * 3600)

    for f in os.listdir(TYPHOON_DIR):
        filepath = os.path.join(TYPHOON_DIR, f)
        if os.path.isfile(filepath):
            if os.path.getmtime(filepath) < cutoff:
                os.remove(filepath)
                logger.info(f'Cleanup: removed {f}')


def _typhoon_capture_job():
    """定期執行颱風截圖的背景 job"""
    while True:
        if _typhoon_scheduler_enabled:
            logger.info('Typhoon scheduler: starting capture cycle')
            try:
                # 先清理舊檔案
                _cleanup_old_files()

                # 並行截圖
                threads = []
                for name, url in TYPHOON_SITES:
                    t = threading.Thread(target=_capture_site, args=(name, url))
                    threads.append(t)
                    t.start()
                for t in threads:
                    t.join()

                logger.info('Typhoon scheduler: capture cycle complete')
            except Exception as e:
                logger.error(f'Typhoon scheduler error: {e}')

        # 等待下次執行
        time.sleep(TYPHOON_INTERVAL_MINUTES * 60)


# --- Flask 路由 ---

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'}), 200


@app.route('/typhoon/scheduler', methods=['POST'])
def typhoon_scheduler_control():
    """開關颱風排程

    POST {"enabled": true/false}
    """
    global _typhoon_scheduler_enabled
    data = request.get_json()
    _typhoon_scheduler_enabled = data.get('enabled', True)
    logger.info(f'Typhoon scheduler set to: {_typhoon_scheduler_enabled}')
    return jsonify({'enabled': _typhoon_scheduler_enabled}), 200


@app.route('/typhoon/scheduler', methods=['GET'])
def typhoon_scheduler_status():
    """查詢排程狀態"""
    return jsonify({'enabled': _typhoon_scheduler_enabled}), 200


@app.route('/typhoon/trigger', methods=['POST'])
def typhoon_trigger():
    """手動觸發一次颱風截圖（不等排程）"""
    def _run():
        _cleanup_old_files()
        threads = []
        for name, url in TYPHOON_SITES:
            t = threading.Thread(target=_capture_site, args=(name, url))
            threads.append(t)
            t.start()
        for t in threads:
            t.join()

    threading.Thread(target=_run, daemon=True).start()
    return jsonify({'message': 'Typhoon capture triggered'}), 202


@app.route('/latest/typhoon', methods=['GET'])
def latest_typhoon():
    """取得最新的颱風截圖影片和預覽圖

    Response:
    {
        "ncdr": {"video": "typhoon_ncdr_20260616_1430.mp4", "preview": "typhoon_ncdr_20260616_1430.png", "time": "2026-06-16T14:30"},
        "windy": {"video": "typhoon_windy_20260616_1430.mp4", "preview": "typhoon_windy_20260616_1430.png", "time": "2026-06-16T14:30"},
        "available": true
    }
    """
    result = {'available': False}

    for site_name, _ in TYPHOON_SITES:
        # 找該 site 最新的影片檔
        pattern = os.path.join(TYPHOON_DIR, f'{site_name}_*.mp4')
        videos = sorted(glob.glob(pattern))
        if not videos:
            continue

        latest_video = videos[-1]
        video_filename = os.path.basename(latest_video)

        # 對應的預覽圖
        preview_filename = video_filename.replace('.mp4', '.png')
        preview_path = os.path.join(TYPHOON_DIR, preview_filename)

        # 解析時間戳
        # 檔名格式：typhoon_ncdr_20260616_1430.mp4
        parts = video_filename.replace('.mp4', '').split('_')
        ts_str = '_'.join(parts[-2:])  # 20260616_1430
        try:
            dt = datetime.strptime(ts_str, '%Y%m%d_%H%M')
            time_str = dt.strftime('%Y-%m-%dT%H:%M')
        except ValueError:
            time_str = ''

        # key: typhoon_ncdr -> ncdr, typhoon_windy -> windy
        key = site_name.replace('typhoon_', '')
        result[key] = {
            'video': video_filename,
            'preview': preview_filename if os.path.exists(preview_path) else None,
            'time': time_str,
        }
        result['available'] = True

    return jsonify(result), 200


@app.route('/typhoon/download/<filename>', methods=['GET'])
def typhoon_download(filename):
    """下載颱風截圖檔案（影片或圖片）"""
    filepath = os.path.join(TYPHOON_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404

    mimetype = 'video/mp4' if filename.endswith('.mp4') else 'image/png'
    return send_file(filepath, mimetype=mimetype)


# --- 原有的通用截圖端點 ---

@app.route('/capture', methods=['POST'])
def capture():
    """
    截圖並合成影片

    Request JSON:
    {
        "sites": [["output_name", "url"], ...],
        "framerate": 4,
        "duration": 30,
        "width": 1138,
        "height": 640
    }

    Response: 回傳包含所有產出檔案路徑的 JSON
    """
    data = request.get_json()
    sites = data.get('sites', [])
    framerate = data.get('framerate', 4)
    duration = data.get('duration', 30)
    width = data.get('width', 1138)
    height = data.get('height', 640)
    extra_headers = data.get('headers', {})

    if not sites:
        return jsonify({'error': 'No sites provided'}), 400

    logger.info(f'Capture request: sites={[s[0] for s in sites]}, framerate={framerate}, duration={duration}, {width}x{height}')

    results = []

    for output_name, url in sites:
        # 清理舊檔案
        for f in os.listdir(PICS_DIR):
            if f.startswith(output_name):
                os.remove(os.path.join(PICS_DIR, f))

        # 使用 Playwright 截圖
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True,
                args=[
                    '--use-gl=swiftshader',
                    '--enable-webgl',
                    '--ignore-gpu-blocklist',
                    '--no-sandbox',
                ]
            )
            context = browser.new_context(
                viewport={'width': width, 'height': height},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                           'AppleWebKit/537.36 (KHTML, like Gecko) '
                           'Chrome/123.0.0.0 Safari/537.36',
                extra_http_headers=extra_headers
            )
            page = context.new_page()
            page.goto(url, wait_until='load', timeout=60000)

            num_frames = framerate * duration
            frame_interval = 1.0 / framerate

            for frame_count in range(num_frames):
                page.screenshot(
                    path=f'{PICS_DIR}/{output_name}_{frame_count:03d}.png'
                )
                time.sleep(frame_interval)

            context.close()
            browser.close()

        # 用 FFmpeg 合成影片
        video_path = f'{VIDEOS_DIR}/{output_name}.mp4'
        ffmpeg_command = [
            'ffmpeg', '-y',
            '-framerate', str(framerate),
            '-i', f'{PICS_DIR}/{output_name}_%03d.png',
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            video_path
        ]
        subprocess.run(ffmpeg_command, capture_output=True)

        results.append({
            'name': output_name,
            'video_path': video_path,
            'total_frames': num_frames
        })

    logger.info(f'Capture complete: {[r["name"] for r in results]}')
    return jsonify({'results': results}), 200


@app.route('/download/video/<filename>', methods=['GET'])
def download_video(filename):
    """下載影片檔案"""
    logger.info(f'Download video: {filename}')
    filepath = os.path.join(VIDEOS_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    return send_file(filepath, mimetype='video/mp4')


@app.route('/download/image/<filename>', methods=['GET'])
def download_image(filename):
    """下載截圖檔案"""
    logger.info(f'Download image: {filename}')
    filepath = os.path.join(PICS_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    return send_file(filepath, mimetype='image/png')


if __name__ == '__main__':
    os.makedirs(PICS_DIR, exist_ok=True)
    os.makedirs(VIDEOS_DIR, exist_ok=True)
    os.makedirs(TYPHOON_DIR, exist_ok=True)

    # 啟動颱風排程背景執行緒
    scheduler_thread = threading.Thread(target=_typhoon_capture_job, daemon=True)
    scheduler_thread.start()
    logger.info('Typhoon scheduler started')

    app.run(host='0.0.0.0', port=5001)

# --- 啟動排程（gunicorn 和直接執行都會觸發）---

os.makedirs(PICS_DIR, exist_ok=True)
os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(TYPHOON_DIR, exist_ok=True)
os.makedirs(os.path.join(TYPHOON_DIR, 'tmp_pics'), exist_ok=True)

# 只在第一個 worker 啟動排程（用檔案鎖避免重複）
_LOCK_FILE = '/tmp/typhoon_scheduler.lock'

def _start_scheduler_once():
    """確保排程只啟動一次（多 worker 環境）"""
    try:
        fd = os.open(_LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        # 成功建立 lock file，啟動排程
        scheduler_thread = threading.Thread(target=_typhoon_capture_job, daemon=True)
        scheduler_thread.start()
        logger.info(f'Typhoon scheduler started (pid={os.getpid()})')
    except FileExistsError:
        # 其他 worker 已經啟動了
        logger.info(f'Typhoon scheduler already running, skipping (pid={os.getpid()})')


_start_scheduler_once()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
