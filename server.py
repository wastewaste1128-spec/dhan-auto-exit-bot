from flask import Flask, request
import threading
from main import start_monitoring

app = Flask(__name__)

@app.route("/")
def home():
    return "Dhan Auto Exit Bot Running!"

@app.route("/start")
def start_bot():
    token = request.args.get("token")
    entry = request.args.get("entry")
    qty = request.args.get("qty")

    if not token or not entry or not qty:
        return "Error: Missing parameters. Use /start?token=XXX&entry=YYY&qty=ZZZ"

    try:
        entry = float(entry)
        qty = int(qty)
    except:
        return "Invalid entry or qty"

    # Run monitor in background thread
    thread = threading.Thread(target=start_monitoring, args=(token, entry, qty))
    thread.start()

    return f"Auto Exit Started! Token={token}, Entry={entry}, Qty={qty}"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
