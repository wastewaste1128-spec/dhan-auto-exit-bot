from flask import Flask
import threading
from main import start_monitoring

app = Flask(__name__)

@app.route("/")
def home():
    return "Dhan Auto Exit Bot Running!"

@app.route("/start")
def start_bot():
    # run monitoring in background so HTTP response returns quickly
    thread = threading.Thread(target=start_monitoring)
    thread.start()
    return "Auto Exit Started for latest intraday options position."

if __name__ == "__main__":
    # for local debug; on Render you’ll use gunicorn
    app.run(host="0.0.0.0", port=10000)
