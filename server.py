from flask import Flask
import threading
from main import start_monitoring

app = Flask(__name__)

@app.route("/")
def home():
    return "Dhan Auto Exit Bot Running"

@app.route("/start")
def start_bot():
    thread = threading.Thread(target=start_monitoring)
    thread.start()
    return "Auto Exit Started for latest intraday options position."

