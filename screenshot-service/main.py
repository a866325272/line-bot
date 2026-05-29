"""
Screenshot Service - 獨立的網頁截圖錄影微服務
接收 HTTP 請求，使用 Playwright 截圖並用 FFmpeg 合成影片，回傳影片檔案。
"""
import os
import time
import subprocess
import shutil
from flask import Flask, request, jsonify, send_file
from playwright.sync_api import sync_playwright

app = Flask(__name__)

PICS_DIR = '/app/pics'
VIDEOS_DIR = '/app/videos'


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'}), 200


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

    if not sites:
        return jsonify({'error': 'No sites provided'}), 400

    results = []

    for output_name, url in sites:
        # 清理舊檔案
        for f in os.listdir(PICS_DIR):
            if f.startswith(output_name):
                os.remove(os.path.join(PICS_DIR, f))

        # 使用 Playwright 截圖
        with sync_playwright() as playwright:
            browser = playwright.firefox.launch()
            context = browser.new_context(
                viewport={'width': width, 'height': height},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                           'AppleWebKit/537.36 (KHTML, like Gecko) '
                           'Chrome/123.0.0.0 Safari/537.36'
            )
            page = context.new_page()
            page.goto(url, wait_until='networkidle', timeout=60000)

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

        # 找出最後一張截圖作為預覽圖
        last_frame = f'{PICS_DIR}/{output_name}_{num_frames - 1:03d}.png'

        results.append({
            'name': output_name,
            'video_path': video_path,
            'preview_path': last_frame,
            'total_frames': num_frames
        })

    return jsonify({'results': results}), 200


@app.route('/download/video/<filename>', methods=['GET'])
def download_video(filename):
    """下載影片檔案"""
    filepath = os.path.join(VIDEOS_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    return send_file(filepath, mimetype='video/mp4')


@app.route('/download/image/<filename>', methods=['GET'])
def download_image(filename):
    """下載截圖檔案"""
    filepath = os.path.join(PICS_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    return send_file(filepath, mimetype='image/png')

if __name__ == '__main__':
    os.makedirs(PICS_DIR, exist_ok=True)
    os.makedirs(VIDEOS_DIR, exist_ok=True)
    app.run(host='0.0.0.0', port=5001)
