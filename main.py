import os
import time
import requests
from dhanhq import dhanhq

# ========= CONFIG ==========
CLIENT_ID = os.getenv("DHAN_CLIENT_ID")
ACCESS_TOKEN = os.getenv("DHAN_ACCESS_TOKEN")

TARGET_POINTS = 1.0          # +1 point target
POLL_INTERVAL = 0.5            # seconds between checks
ALLOWED_SEGMENTS = {"NSE_FNO", "BSE_FNO"}  # NSE/BSE options only
# ===========================

if not CLIENT_ID or not ACCESS_TOKEN:
    raise RuntimeError(
        "DHAN_CLIENT_ID or DHAN_ACCESS_TOKEN not set in environment variables"
    )

dhan = dhanhq(CLIENT_ID, ACCESS_TOKEN)


def get_positions():
    """Safely fetch today's open positions."""
    try:
        pos = dhan.get_positions()
        print("Raw positions from API:", pos, flush=True)

        # Library usually returns a list, but we guard against other types
        if isinstance(pos, list):
            return pos
        if isinstance(pos, dict) and "data" in pos:
            return pos["data"]

        print("Unexpected positions type:", type(pos), flush=True)
        return []
    except Exception as e:
        print("Error fetching positions:", e, flush=True)
        return []


def is_option_position(p: dict) -> bool:
    """Filter: intraday CE/PE options only, NSE_FNO / BSE_FNO, long positions."""
    if not isinstance(p, dict):
        return False

    # Only intraday
    if p.get("productType") != "INTRADAY":
        return False

    # Only F&O segments for NSE / BSE
    if p.get("exchangeSegment") not in ALLOWED_SEGMENTS:
        return False

    # Only long positions (net quantity > 0)
    try:
        net_qty = float(p.get("netQty", 0))
    except Exception:
        net_qty = 0
    if net_qty <= 0:
        return False

    # Only options (CE / PE)
    symbol = str(p.get("tradingSymbol", "")).upper()
    opt_type = p.get("drvOptionType")
    if opt_type in ("CALL", "PUT"):
        return True
    if symbol.endswith("CE") or symbol.endswith("PE"):
        return True

    return False


def get_open_option_positions():
    """Return list of all open intraday option positions that match our filter."""
    all_pos = get_positions()
    opts = [p for p in all_pos if is_option_position(p)]

    print(f"Filtered option positions ({len(opts)}):", flush=True)
    for p in opts:
        print(
            f"- {p.get('tradingSymbol')} | seg={p.get('exchangeSegment')} "
            f"netQty={p.get('netQty')} buyAvg={p.get('buyAvg')}",
            flush=True,
        )

    return opts


def get_ltp_map(positions):
    """
    Call Dhan Market Quote API to fetch LTP for all given positions.
    Returns dict keyed by (exchangeSegment, securityId) -> last_price.
    """
    payload = {}

    for p in positions:
        seg = p.get("exchangeSegment")
        sid = p.get("securityId")
        if not seg or sid is None:
            continue
        try:
            sid_int = int(sid)
        except Exception:
            # keep as string but still send
            sid_int = sid
        payload.setdefault(seg, []).append(sid_int)

    if not payload:
        return {}

    url = "https://api.dhan.co/v2/marketfeed/ltp"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "access-token": ACCESS_TOKEN,
        "client-id": CLIENT_ID,
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=3)
        print("LTP API status:", resp.status_code, flush=True)
        print("LTP API raw response:", resp.text, flush=True)
        resp.raise_for_status()

        data = resp.json().get("data", {})
        ltp_map = {}

        for seg, sec_dict in data.items():
            if not isinstance(sec_dict, dict):
                continue
            for sid, quote in sec_dict.items():
                if not isinstance(quote, dict):
                    continue
                ltp = quote.get("last_price")
                if ltp is not None:
                    ltp_map[(seg, str(sid))] = float(ltp)

        return ltp_map

    except Exception as e:
        print("Error fetching LTP:", e, flush=True)
        return {}


def exit_position(p):
    """Place a market SELL order to fully exit the given position."""
    seg = p["exchangeSegment"]
    sec_id = str(p["securityId"])
    qty = int(p["netQty"])

    body = {
        "dhanClientId": CLIENT_ID,
        "transactionType": "SELL",
        "exchangeSegment": seg,
        "productType": "INTRADAY",
        "orderType": "MARKET",
        "validity": "DAY",
        "securityId": sec_id,
        "quantity": qty,
        "disclosedQuantity": 0,
        "price": 0,
        "triggerPrice": 0,
        "afterMarketOrder": False,
        "amoTime": "",
        "boProfitValue": 0,
        "boStopLossValue": 0,
        # Derivative fields (optional but we pass if available)
        "drvExpiryDate": p.get("drvExpiryDate", ""),
        "drvOptionType": p.get("drvOptionType"),
        "drvStrikePrice": p.get("drvStrikePrice", 0),
    }

    url = "https://api.dhan.co/v2/orders"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "access-token": ACCESS_TOKEN,
    }

    print(f"Placing exit order for {p.get('tradingSymbol')} qty={qty}", flush=True)
    try:
        resp = requests.post(url, headers=headers, json=body, timeout=5)
        print("Exit order response:", resp.status_code, resp.text, flush=True)
    except Exception as e:
        print("Error placing exit order:", e, flush=True)


def start_monitoring():
    """Main monitoring loop – run in a separate thread from Flask."""
    print("Monitoring started...", flush=True)

    while True:
        positions = get_open_option_positions()

        if not positions:
            print("No matching intraday option positions. Sleeping...", flush=True)
            time.sleep(POLL_INTERVAL)
            continue

        ltp_map = get_ltp_map(positions)

        for p in positions:
            seg = p.get("exchangeSegment")
            sid = str(p.get("securityId"))

            try:
                buy_avg = float(p.get("buyAvg", 0))
            except Exception:
                buy_avg = 0.0

            target = buy_avg + TARGET_POINTS
            ltp = ltp_map.get((seg, sid))

            print(
                f"{p.get('tradingSymbol')} | seg={seg} sid={sid} "
                f"buyAvg={buy_avg} target={target} LTP={ltp}",
                flush=True,
            )

            if ltp is not None and ltp >= target:
                print(
                    f"TARGET HIT: {p.get('tradingSymbol')} "
                    f"LTP {ltp} >= {target}. Sending exit order...",
                    flush=True,
                )
                exit_position(p)

        time.sleep(POLL_INTERVAL)
