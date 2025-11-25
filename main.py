import time
import os
import requests
from dhanhq import dhanhq

# ENV keys
client_id = os.getenv("DHAN_CLIENT_ID")
access_token = os.getenv("DHAN_ACCESS_TOKEN")

dhan = dhanhq(client_id, access_token)

POLL_INTERVAL = 1.5   # seconds
TARGET_POINTS = 1     # +1 point target


def get_positions():
    try:
        pos = dhan.get_positions()
        if isinstance(pos, str):
            print("Positions API returned string:", pos)
            return []
        return pos.get("data", [])
    except Exception as e:
        print("Position Error:", e)
        return []


def filter_open_option_positions():
    positions = get_positions()
    open_pos = []

    print(f"Raw positions from API: {positions}")

    for p in positions:
        if (
            p.get("productType") == "INTRADAY"
            and p.get("exchangeSegment") in ["NSE_FNO", "BSE_FNO"]
            and p.get("netQty", 0) != 0
        ):
            open_pos.append(p)

    print(f"Filtered option positions ({len(open_pos)}):")
    for p in open_pos:
        print(f"- {p['tradingSymbol']} | seg={p['exchangeSegment']} netQty={p['netQty']} buyAvg={p['buyAvg']}")

    return open_pos


def get_ltp(segment, security_id):
    url = "https://api.dhan.co/v2/marketfeed/ltp"
    headers = {"access-token": access_token}

    payload = {
        "NSE_FNO": [security_id] if segment == "NSE_FNO" else [],
        "BSE_FNO": [security_id] if segment == "BSE_FNO" else []
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        print("LTP API status:", response.status_code)
        print("LTP API raw response:", response.text)

        if response.status_code != 200:
            return None

        data = response.json()
        segdata = data["data"].get(segment, {})
        if str(security_id) in segdata:
            return segdata[str(security_id)]["last_price"]
        return None

    except Exception as e:
        print("Error fetching LTP:", e)
        return None


def place_exit_order(position):
    print(f"Placing exit order for {position['tradingSymbol']} qty={position['netQty']}")

    order_data = {
        "transactionType": "SELL",
        "exchangeSegment": position["exchangeSegment"],
        "productType": "INTRADAY",
        "orderType": "MARKET",
        "securityId": int(position["securityId"]),
        "quantity": abs(int(position["netQty"])),
        "disclosedQuantity": 0,
        "afterMarketOrder": False,
        "amoTime": "OPEN",
        "channel": "API"
    }

    try:
        res = dhan.place_order(order_data)
        print("Exit order response:", res)
        return res
    except Exception as e:
        print("Exit order failed:", e)
        return None


def start_monitoring():
    print("Monitoring started...")

    while True:
        positions = filter_open_option_positions()

        if not positions:
            print("No open option positions. Sleeping...")
            time.sleep(POLL_INTERVAL)
            continue

        for pos in positions:
            segment = pos["exchangeSegment"]
            sid = pos["securityId"]
            buy_avg = float(pos["buyAvg"])
            net_qty = int(pos["netQty"])

            target = buy_avg + TARGET_POINTS

            ltp = get_ltp(segment, sid)

            print(f"{pos['tradingSymbol']} | seg={segment} sid={sid} buyAvg={buy_avg} target={target} LTP={ltp}")

            if ltp is None:
                continue

            if ltp >= target:
                print(f"TARGET HIT: {pos['tradingSymbol']} LTP {ltp} >= {target}. Sending exit order...")
                place_exit_order(pos)

        time.sleep(POLL_INTERVAL)
