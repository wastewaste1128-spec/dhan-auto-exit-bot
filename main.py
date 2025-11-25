import os
import time
import requests
from dhanhq import dhanhq

# ========= CONFIG ==========
CLIENT_ID = os.getenv("DHAN_CLIENT_ID")
CLIENT_SECRET = os.getenv("DHAN_CLIENT_SECRET")

TARGET_POINTS = 1.0          # +1 point target
POLL_INTERVAL = 1.5          # seconds
ALLOWED_SEGMENTS = {"NSE_FNO", "BSE_FNO"}  # F&O only
# ===========================

if not CLIENT_ID or not CLIENT_SECRET:
    raise RuntimeError(
        "DHAN_CLIENT_ID or DHAN_CLIENT_SECRET missing in environment variables"
    )

# DhanHQ library still uses access token style for certain endpoints, 
# but for LTP + Orders we MUST use V2 headers manually.
dhan = dhanhq(CLIENT_ID, CLIENT_SECRET)


# -------------------------------------------------
# FETCH POSITIONS
# -------------------------------------------------
def get_positions():
    """Fetch open positions safely."""
    try:
        pos = dhan.get_positions()
        print("Raw positions from API:", pos, flush=True)

        if isinstance(pos, list):
            return pos
        if isinstance(pos, dict) and "data" in pos:
            return pos["data"]
        return []
    except Exception as e:
        print("Error fetching positions:", e, flush=True)
        return []


# -------------------------------------------------
# FILTER ONLY OPTION POSITIONS
# -------------------------------------------------
def is_option_position(p: dict) -> bool:
    if not isinstance(p, dict):
        return False

    if p.get("productType") != "INTRADAY":
        return False

    if p.get("exchangeSegment") not in ALLOWED_SEGMENTS:
        return False

    try:
        net_qty = float(p.get("netQty", 0))
    except Exception:
        net_qty = 0

    if net_qty <= 0:
        return False

    opt_type = p.get("drvOptionType")
    if opt_type in ("CALL", "PUT"):
        return True

    sym = str(p.get("tradingSymbol", "")).upper()
    return sym.endswith("CE") or sym.endswith("PE")


def get_open_option_positions():
    positions = get_positions()
    option_positions = [p for p in positions if is_option_position(p)]

    print(f"Filtered option positions ({len(option_positions)}):", flush=True)
    for p in option_positions:
        print(
            f"- {p.get('tradingSymbol')} | seg={p.get('exchangeSegment')} "
            f"netQty={p.get('netQty')} buyAvg={p.get('buyAvg')}",
            flush=True,
        )

    return option_positions


# -------------------------------------------------
# FETCH LTP (V2 API)
# -------------------------------------------------
def get_ltp_map(positions):
    payload = {}

    for p in positions:
        seg = p.get("exchangeSegment")
        sid = p.get("securityId")

        if not seg or sid is None:
            continue

        try:
            sid = int(sid)
        except:
            pass

        payload.setdefault(seg, []).append(sid)

    if not payload:
        return {}

    url = "https://api.dhan.co/v2/marketfeed/ltp"

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Dhan-Client-Id": CLIENT_ID,
        "X-Dhan-Client-Secret": CLIENT_SECRET,
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=3)
        print("LTP API status:", resp.status_code, flush=True)
        print("LTP API raw response:", resp.text, flush=True)

        resp.raise_for_status()
        data = resp.json().get("data", {})

        ltp_map = {}

        for seg, sec_data in data.items():
            if not isinstance(sec_data, dict):
                continue
            for sid, quote in sec_data.items():
                if not isinstance(quote, dict):
                    continue

                price = quote.get("last_price")
                if price is not None:
                    ltp_map[(seg, str(sid))] = float(price)

        return ltp_map

    except Exception as e:
        print("Error fetching LTP:", e, flush=True)
        return {}


# -------------------------------------------------
# EXIT ORDER
# -------------------------------------------------
def exit_position(p):
    seg = p["exchangeSegment"]
    sid = str(p["securityId"])
    qty = int(p["netQty"])

    body = {
        "dhanClientId": CLIENT_ID,
        "transactionType": "SELL",
        "exchangeSegment": seg,
        "productType": "INTRADAY",
        "orderType": "MARKET",
        "validity": "DAY",
        "securityId": sid,
        "quantity": qty,
        "disclosedQuantity": 0,
        "price": 0,
        "triggerPrice": 0,
        "afterMarketOrder": False,
        "amoTime": "",
        "boProfitValue": 0,
        "boStopLossValue": 0,
        "drvExpiryDate": p.get("drvExpiryDate", ""),
        "drvOptionType": p.get("drvOptionType"),
        "drvStrikePrice": p.get("drvStrikePrice", 0),
    }

    url = "https://api.dhan.co/v2/orders"

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Dhan-Client-Id": CLIENT_ID,
        "X-Dhan-Client-Secret": CLIENT_SECRET,
    }

    print(f"Placing exit order for {p.get('tradingSymbol')} qty={qty}", flush=True)

    try:
        resp = requests.post(url, headers=headers, json=body, timeout=5)
        print("Exit order response:", resp.status_code, resp.text, flush=True)
    except Exception as e:
        print("Error placing exit order:", e, flush=True)


# -------------------------------------------------
# MAIN MONITOR LOOP
# -------------------------------------------------
def start_monitoring():
    print("Monitoring started...", flush=True)

    while True:
        positions = get_open_option_positions()

        if not positions:
            print("No option positions. Sleeping...", flush=True)
            time.sleep(POLL_INTERVAL)
            continue

        ltp_map = get_ltp_map(positions)

        for p in positions:
            seg = p["exchangeSegment"]
            sid = str(p["securityId"])
            buy_avg = float(p.get("buyAvg", 0))
            target = buy_avg + TARGET_POINTS
            ltp = ltp_map.get((seg, sid))

            print(
                f"{p['tradingSymbol']} | seg={seg} sid={sid} "
                f"buyAvg={buy_avg} target={target} LTP={ltp}",
                flush=True,
            )

            if ltp is not None and ltp >= target:
                print(
                    f"TARGET HIT → {p['tradingSymbol']} "
                    f"LTP {ltp} >= {target} → Exiting...",
                    flush=True,
                )
                exit_position(p)

        time.sleep(POLL_INTERVAL)
