"""加密貨幣查價"""

import datetime as dt
import requests


def get_cryptocurrency_market() -> str:
    """取得加密貨幣交易對列表"""
    data = requests.get('https://max-api.maicoin.com/api/v2/markets')
    json_data = data.json()
    lines = [f'id:{i["id"]},交易對:{i["name"]}' for i in json_data]
    return '\n'.join(lines)


def cryptocurrency(market: str) -> str:
    """取得加密貨幣價格"""
    try:
        trades = requests.get(f'https://max-api.maicoin.com/api/v2/trades?market={market}')
        trades_data = trades.json()
        timestamp = trades_data[0]['created_at']
        datetime_obj = dt.datetime.fromtimestamp(timestamp)
        price = trades_data[0]['price']
        volume = trades_data[0]['volume']
        market_name = trades_data[0]['market_name']
        side = '賣' if trades_data[0]['side'] == 'bid' else '買'

        depth = requests.get(f'https://max-api.maicoin.com/api/v2/depth?market={market}')
        depth_data = depth.json()
        ask_price = depth_data['asks'][-1][0]
        ask_volume = depth_data['asks'][-1][1]
        bid_price = depth_data['bids'][0][0]
        bid_volume = depth_data['bids'][0][1]

        msg = (
            f'{market_name} 最新成交({side}):\n'
            f'成交時間:{datetime_obj}\n成交價:{price}\t成交量:{volume}\n'
            f'{market_name} 掛單簿:\n'
            f'賣 價格:{ask_price}\t數量:{ask_volume}\n'
            f'買 價格:{bid_price}\t數量:{bid_volume}'
        )
        return msg
    except:
        return "格式錯誤"
