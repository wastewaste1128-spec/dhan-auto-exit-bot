import time
import os
from dhanhq import dhanhq

client_id = os.getenv("DHAN_CLIENT_ID")
access_token = os.getenv("DHAN_ACCESS_TOKEN")

dhan = dhanhq(client_id, access_token)

TARGET_POINTS = 1   # +1 point target

def get_latest_option_position():
    """
    Find the most recent intraday options position (NFO) with netQty > 0
    i.e. your latest BUY position in any index option.
    """
    try:
        positions = dhan.get_positions()
    except Exception as e:
        print("Error fetching positions:", e)
        return None

    # filter only open intraday option positions
    candidates = [
        p for p in positions
        if p.get("exchangeSegment") == "NFO"
        and p.get("productType") == "INTRADAY"
        and float(p.get("netQty", 0)) > 0
    ]

    if not candidates:
        print("No open intraday option positions found.")
        return None

    # just take the last one (usually the most recent trade)
    pos = candidates[-1]

    security_id = pos["securityId"]
    buy_avg = float(pos["buyAvg"])
    qty = int(pos["netQty"])
    trading_symbol = pos.get("tradingSymbol", security_id)

    print(f"Selected position: {trading_symbol}, "
          f"securityId={security_id}, buyAvg={buy_avg}, qty={qty}")

    return security_id, buy_avg, qty, trading_symbol


def get_ltp(symbol):
    try:
        q = dhan.get_quote(symbol)
        return q["LTP"]
    except Exception as e:
        print("Error fetching LTP:", e)
        return None


def place_exit(symbol, qty):
    print(">>> SENDING EXIT ORDER <<<")
    try:
        res = dhan.place_order(
            tag="AUTOEXIT",
            transaction_type="SELL",
            exchange_segment="NFO",
            product_type="INTRADAY",
            order_type="MARKET",
            validity="DAY",
            security_id=symbol,
            quantity=qty
        )
        print("Exit API response:", res)
        return res
    except Exception as e:
        print("Exit Error:", e)
        return None


def start_monitoring():
    # 1) detect latest open option position
    data = get_latest_option_position()
    if not data:
        print("No position to monitor. Exiting.")
        return

    security_id, entry_price, qty, tsym = data
    target = entry_price + TARGET_POINTS

    print(f"Monitoring {tsym} (securityId {security_id})")
    print(f"Entry={entry_price}, Target={target}, Qty={qty}")

    # 2) monitor LTP and exit at target
    while True:
        ltp = get_ltp(security_id)
        if ltp is not None:
            print("LTP:", ltp)

            if ltp >= target:
                print("Target Hit! Exiting...")
                place_exit(security_id, qty)
                return

        time.sleep(0.5)
