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
import threading
import time
from datetime import datetime, timezone, timedelta

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

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('earthquake-service')

# --- Shared State ---
state = {
    "eew": {
        "data": [],           # 目前進行中的 EEW 速報列表
        "last_update": None,  # 最後更新時間
        "connected": False,
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
                with state_lock:
                    state["eew"]["data"] = event_data if isinstance(event_data, list) else [event_data]
                    state["eew"]["last_update"] = datetime.now(timezone(timedelta(hours=8))).isoformat()

                # 有 EEW 速報時記錄
                if event_data and event_data != []:
                    logger.warning(f"[EEW] ⚠️  地震速報! {json.dumps(event_data, ensure_ascii=False)}")

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
    - 無 EEW 時回傳最新 report + RTS 有感震度
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
