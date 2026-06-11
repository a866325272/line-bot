"""LINE Bot Flask 應用程式進入點"""

import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config import logger
from exceptions import AppError
from api import register_blueprints
from webhook import webhook_bp

app = Flask(__name__, static_folder=None)

# --- CORS ---
CORS(app,
     resources={r"/api/*": {"origins": os.getenv("CORS_ORIGINS", "*")}},
     supports_credentials=True)

# --- Rate Limiter ---
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    storage_uri="memory://",
    default_limits=["100 per minute"]
)


@limiter.request_filter
def exempt_webhook():
    return request.method == 'POST' and request.path == '/'


# --- 註冊 Blueprints ---
register_blueprints(app)
app.register_blueprint(webhook_bp)

# --- 全域錯誤處理 ---
@app.errorhandler(AppError)
def handle_app_error(e):
    logger.warning(f"AppError: {e.code} - {e.message}")
    return jsonify(e.to_dict()), e.status_code


@app.errorhandler(429)
def handle_rate_limit(e):
    return jsonify({"error": "請求過於頻繁，請稍後再試", "code": "RATE_LIMITED"}), 429


# --- Vue SPA serve ---
@app.route("/", methods=['GET'])
def serve_vue_index():
    return send_from_directory('dist', 'index.html')


@app.route("/<path:path>", methods=['GET'])
def serve_vue_assets(path):
    if path.startswith('line-bot/'):
        path = path[len('line-bot/'):]
    if path == 'line-bot':
        path = ''
    dist_path = os.path.join(app.root_path, 'dist')
    if path and os.path.isfile(os.path.join(dist_path, path)):
        return send_from_directory('dist', path)
    return send_from_directory('dist', 'index.html')


# --- 本地測試 ---
if __name__ == "__main__":
    class StripPrefixMiddleware:
        def __init__(self, wsgi_app, prefix='/line-bot'):
            self.wsgi_app = wsgi_app
            self.prefix = prefix

        def __call__(self, environ, start_response):
            path = environ.get('PATH_INFO', '')
            if path.startswith(self.prefix + '/'):
                environ['PATH_INFO'] = path[len(self.prefix):]
                environ['SCRIPT_NAME'] = self.prefix
            elif path == self.prefix:
                environ['PATH_INFO'] = '/'
                environ['SCRIPT_NAME'] = self.prefix
            return self.wsgi_app(environ, start_response)

    app.wsgi_app = StripPrefixMiddleware(app.wsgi_app)
    app.run(host='0.0.0.0')
