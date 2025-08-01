
import os
from flask import Flask, render_template, request, redirect, session
from datetime import datetime
import json

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "defaultsecret")

def load_state():
    try:
        with open("data/state.json", "r") as f:
            return json.load(f)
    except:
        return {}

@app.route("/")
def index():
    state = load_state()
    monitor_start = int(os.environ.get("MONITOR_START_HOUR", state.get("monitor_start", 8)))
    monitor_end = int(os.environ.get("MONITOR_END_HOUR", state.get("monitor_end", 20)))
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"<h2>USDT 监控控制台</h2><p>当前服务器时间：{now}</p><p>监控时段：{monitor_start}:00 - {monitor_end}:00</p>"
