"""
Earthquake SSE Listener Service
================================
持續監聽 ExpTech SSE 串流，快取最新地震即時資料，
並提供 HTTP API 給 main app (webhook) 查詢。

SSE 來源:
- EEW (地震速報): https://api.lb.exptech.dev/api/v2/eq/eew
- RTS (即時震度): https://api.lb.exptech.dev/api/v2/trem/rts

HTTP API:
- GET /status        → 服務狀態
- GET /eew           → 最新 EEW 速報（即時，地震發生時 1~3 秒內可取得）
- GET /rts           → 最新 RTS 即時震度資料
- GET /report        → 最新地震報告（來自 ExpTech report API，延遲數分鐘）
- GET /latest        → 綜合最新地震資訊（EEW 優先，無 EEW 則回 report）
"""

import json
import logging
import logging.handlers
import threading
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests
from flask import Flask, jsonify

# --- Config ---
EXPTECH_SSE_EEW_URL = "https://api.lb.exptech.dev/api/v2/eq/eew"
EXPTECH_SSE_RTS_URL = "https://api.lb.exptech.dev/api/v2/trem/rts"
EXPTECH_REPORT_API_URLS = [
    "https://api.core-tnn1.exptech.dev",
    "https://api.core-tyo1.exptech.dev",
    "https://api.lb.exptech.dev",
]
SSE_RECONNECT_DELAY = 3  # seconds
REPORT_POLL_INTERVAL = 60  # seconds
LAST_EEW_FILE = Path("/opt/earthquake-service/last_eew.json")  # 持久化最後一筆速報（掛載 volume）

# --- Logging ---
logger = logging.getLogger('')
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
rotate_handler = logging.handlers.TimedRotatingFileHandler(
    '/var/log/earthquake-service/earthquake-service.log',
    when="h", interval=1, backupCount=720
)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
rotate_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
logger.addHandler(rotate_handler)
logger.addHandler(console_handler)

# --- Shared State ---
state = {
    "eew": {
        "data": [],           # 目前進行中的 EEW 速報列表
        "last_update": None,  # 最後更新時間
        "connected": False,
        "last_alert": None,   # 最後一筆有效的 EEW 速報（地震結束後仍保留）
        "last_alert_time": None,  # 最後一筆速報的時間
    },
    "rts": {
        "data": None,         # 最新 RTS 資料
        "last_update": None,
        "connected": False,
    },
    "report": {
        "data": [],           # 最近地震報告列表
        "last_update": None,
    },
    "started_at": datetime.now(timezone(timedelta(hours=8))).isoformat(),
}
state_lock = threading.Lock()


# --- Persistence: 啟動時載入上次的 EEW 速報 ---
def _load_last_eew():
    """從檔案載入最後一筆 EEW 速報"""
    try:
        if LAST_EEW_FILE.exists():
            data = json.loads(LAST_EEW_FILE.read_text(encoding="utf-8"))
            state["eew"]["last_alert"] = data.get("last_alert")
            state["eew"]["last_alert_time"] = data.get("last_alert_time")
            logger.info(f"[EEW] Loaded last alert from {LAST_EEW_FILE}")
    except Exception as e:
        logger.warning(f"[EEW] Failed to load last alert: {e}")


def _save_last_eew():
    """將最後一筆 EEW 速報寫入檔案"""
    try:
        data = {
            "last_alert": state["eew"]["last_alert"],
            "last_alert_time": state["eew"]["last_alert_time"],
        }
        LAST_EEW_FILE.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        logger.warning(f"[EEW] Failed to save last alert: {e}")


_load_last_eew()


# --- SSE Parser ---
def parse_sse_stream(response):
    """從 SSE response 逐行解析 data: 事件"""
    buffer = ""
    for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
        if chunk:
            buffer += chunk
            while "\n\n" in buffer:
                block, buffer = buffer.split("\n\n", 1)
                for line in block.strip().split("\n"):
                    if line.startswith("data:"):
                        data_str = line[5:].strip()
                        if data_str:
                            try:
                                yield json.loads(data_str)
                            except json.JSONDecodeError:
                                pass


# --- Taiwan EEW Filter ---
# 排除的非台灣來源（黑名單）
_BLOCKED_AUTHORS = {"nied"}


def _is_taiwan_eew(eew_item):
    """判斷單筆 EEW 是否為台灣地區（排除已知非台灣來源）"""
    if not isinstance(eew_item, dict):
        return False
    author = eew_item.get("author", "").lower()
    return author not in _BLOCKED_AUTHORS


def _filter_taiwan_eew(event_data):
    """從 EEW 事件中過濾出台灣相關的速報，回傳 list 或空 list"""
    if not event_data:
        return []
    items = event_data if isinstance(event_data, list) else [event_data]
    tw_items = [item for item in items if _is_taiwan_eew(item)]
    return tw_items


# --- SSE Listener: EEW ---
def eew_listener():
    """持續監聽 EEW SSE 串流"""
    while True:
        try:
            logger.info("[EEW] Connecting to SSE stream...")
            resp = requests.get(
                EXPTECH_SSE_EEW_URL,
                headers={"Accept": "text/event-stream", "Cache-Control": "no-cache"},
                stream=True,
                timeout=(10, None),  # connect timeout 10s, no read timeout
            )
            resp.raise_for_status()

            with state_lock:
                state["eew"]["connected"] = True
            logger.info("[EEW] Connected successfully")

            for event_data in parse_sse_stream(resp):
                # 過濾：只保留台灣地區的 EEW（author=cwa 或震央在台灣範圍內）
                tw_eew = _filter_taiwan_eew(event_data)

                with state_lock:
                    state["eew"]["data"] = tw_eew
                    state["eew"]["last_update"] = datetime.now(timezone(timedelta(hours=8))).isoformat()

                # 診斷 log：收到非空事件但被 filter 擋掉時記錄
                if event_data and not tw_eew:
                    items = event_data if isinstance(event_data, list) else [event_data]
                    authors = [item.get("author", "unknown") for item in items if isinstance(item, dict)]
                    logger.info(f"[EEW] Received event (filtered out): authors={authors}")

                # 有台灣 EEW 速報時記錄，並保留為 last_alert
                if tw_eew:
                    with state_lock:
                        state["eew"]["last_alert"] = tw_eew
                        state["eew"]["last_alert_time"] = datetime.now(timezone(timedelta(hours=8))).isoformat()
                        _save_last_eew()
                    logger.warning(f"[EEW] ⚠️  台灣地震速報! {json.dumps(tw_eew, ensure_ascii=False)}")

        except Exception as e:
            logger.error(f"[EEW] Connection error: {e}")
        finally:
            with state_lock:
                state["eew"]["connected"] = False
            logger.info(f"[EEW] Reconnecting in {SSE_RECONNECT_DELAY}s...")
            time.sleep(SSE_RECONNECT_DELAY)


# --- SSE Listener: RTS ---
def rts_listener():
    """持續監聽 RTS SSE 串流（即時震度資料，約每 200ms 一筆）"""
    while True:
        try:
            logger.info("[RTS] Connecting to SSE stream...")
            resp = requests.get(
                EXPTECH_SSE_RTS_URL,
                headers={"Accept": "text/event-stream", "Cache-Control": "no-cache"},
                stream=True,
                timeout=(10, None),
            )
            resp.raise_for_status()

            with state_lock:
                state["rts"]["connected"] = True
            logger.info("[RTS] Connected successfully")

            for event_data in parse_sse_stream(resp):
                with state_lock:
                    state["rts"]["data"] = event_data
                    state["rts"]["last_update"] = datetime.now(timezone(timedelta(hours=8))).isoformat()

        except Exception as e:
            logger.error(f"[RTS] Connection error: {e}")
        finally:
            with state_lock:
                state["rts"]["connected"] = False
            logger.info(f"[RTS] Reconnecting in {SSE_RECONNECT_DELAY}s...")
            time.sleep(SSE_RECONNECT_DELAY)


# --- Report Poller ---
def report_poller():
    """定期查詢最新地震報告（每 60 秒）"""
    while True:
        try:
            for base_url in EXPTECH_REPORT_API_URLS:
                try:
                    resp = requests.get(f"{base_url}/api/v2/eq/report?limit=5", timeout=10)
                    if resp.status_code == 200:
                        data = resp.json()
                        with state_lock:
                            state["report"]["data"] = data
                            state["report"]["last_update"] = datetime.now(timezone(timedelta(hours=8))).isoformat()
                        break
                except Exception:
                    continue
        except Exception as e:
            logger.error(f"[Report] Poll error: {e}")

        time.sleep(REPORT_POLL_INTERVAL)


# --- Flask App ---
app = Flask(__name__)


@app.route("/status")
def status():
    """服務狀態"""
    with state_lock:
        return jsonify({
            "service": "earthquake-service",
            "started_at": state["started_at"],
            "eew_connected": state["eew"]["connected"],
            "eew_last_update": state["eew"]["last_update"],
            "rts_connected": state["rts"]["connected"],
            "rts_last_update": state["rts"]["last_update"],
            "report_last_update": state["report"]["last_update"],
        })


@app.route("/eew")
def get_eew():
    """取得最新 EEW 地震速報"""
    with state_lock:
        return jsonify({
            "data": state["eew"]["data"],
            "last_update": state["eew"]["last_update"],
            "connected": state["eew"]["connected"],
            "has_alert": bool(state["eew"]["data"] and state["eew"]["data"] != []),
        })


@app.route("/rts")
def get_rts():
    """取得最新即時震度"""
    with state_lock:
        rts_data = state["rts"]["data"]
        # RTS 資料量大，只回傳有感震度的站點（I >= 0）
        filtered = {}
        if rts_data and "station" in rts_data:
            for station_id, info in rts_data["station"].items():
                if info.get("I", -3) >= 0:
                    filtered[station_id] = info

        return jsonify({
            "data": {
                "station": filtered,
                "int": rts_data.get("int", []) if rts_data else [],
                "time": rts_data.get("time") if rts_data else None,
            } if rts_data else None,
            "last_update": state["rts"]["last_update"],
            "connected": state["rts"]["connected"],
        })


@app.route("/report")
def get_report():
    """取得最新地震報告"""
    with state_lock:
        return jsonify({
            "data": state["report"]["data"],
            "last_update": state["report"]["last_update"],
        })


@app.route("/latest")
def get_latest():
    """
    綜合最新地震資訊:
    - 有 EEW 時回傳 EEW（即時速報）
    - 無 EEW 時回傳最新 report + RTS 有感震度 + 最後一筆速報 (last_eew)
    """
    with state_lock:
        eew_data = state["eew"]["data"]
        has_eew = bool(eew_data and eew_data != [])

        # RTS 有感站點
        rts_data = state["rts"]["data"]
        felt_stations = {}
        if rts_data and "station" in rts_data:
            for station_id, info in rts_data["station"].items():
                if info.get("I", -3) >= 0:
                    felt_stations[station_id] = info

        result = {
            "has_eew": has_eew,
            "eew": eew_data if has_eew else None,
            "last_eew": state["eew"]["last_alert"],
            "last_eew_time": state["eew"]["last_alert_time"],
            "report": state["report"]["data"][0] if state["report"]["data"] else None,
            "felt_stations": felt_stations if felt_stations else None,
            "rts_time": rts_data.get("time") if rts_data else None,
            "eew_last_update": state["eew"]["last_update"],
            "report_last_update": state["report"]["last_update"],
        }
        return jsonify(result)


# --- Start background threads ---
def start_listeners():
    threads = [
        threading.Thread(target=eew_listener, daemon=True, name="eew-listener"),
        threading.Thread(target=rts_listener, daemon=True, name="rts-listener"),
        threading.Thread(target=report_poller, daemon=True, name="report-poller"),
    ]
    for t in threads:
        t.start()
    logger.info("All background listeners started")


start_listeners()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=False)
