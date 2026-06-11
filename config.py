"""集中管理環境變數、logging 初始化"""

import os
import logging
import logging.handlers
from dotenv import load_dotenv

load_dotenv()

# --- 環境變數 ---
EPA_TOKEN = os.getenv('EPA_TOKEN')
CWA_TOKEN = os.getenv('CWA_TOKEN')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
SECRET = os.getenv('SECRET')
OPENAI_TOKEN = os.getenv('OPENAI_TOKEN')
GMAP_API_KEY = os.getenv('GMAP_API_KEY')
LOG_PATH = os.getenv('LOG_PATH')
SCREENSHOT_SERVICE_URL = os.getenv('SCREENSHOT_SERVICE_URL', 'http://screenshot-service:5001')

# --- Logging ---
logger = logging.getLogger('')
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
rotate_handler = logging.handlers.TimedRotatingFileHandler(
    LOG_PATH + 'line-bot.log', when="h", interval=1, backupCount=720
)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
rotate_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
logger.addHandler(rotate_handler)
logger.addHandler(console_handler)


# --- 共用例外處理 ---
def exception_handler(e):
    logger.warning('exception:' + str(e))
