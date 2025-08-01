
from flask import Flask, render_template, request, redirect, session, url_for
from threading import Thread
from datetime import datetime
import time
import os
import json

from monitor import get_trc20_transactions
from notifier import send_email, send_telegram

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'supersecret')

USERNAME = os.getenv('WEBUI_USERNAME', 'admin')
PASSWORD = os.getenv('WEBUI_PASSWORD', 'password')

STATE_FILE = "data/state.json"

def load_state():
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def monitor_loop():
    while True:
        state = load_state()
        if not state["is_running"]:
            time.sleep(5)
            continue

        now = datetime.now().hour
        if state["start_hour"] <= now < state["end_hour"]:
            for address in state["watch_addresses"]:
                txs = get_trc20_transactions(address)
                if txs:
                    tx = txs[0]
                    if tx['tokenInfo']['symbol'] == 'USDT':
                        msg = (
                            f"💸 USDT 转账监控\n"
                            f"地址: {address}\n"
                            f"From: {tx['from_address']}\n"
                            f"To: {tx['to_address']}\n"
                            f"金额: {float(tx['amount_str']) / 1e6} USDT\n"
                            f"交易哈希: {tx['transactionHash']}\n"
                            f"https://tronscan.org/#/transaction/{tx['transactionHash']}"
                        )
                        send_telegram(msg)
                        send_email(msg)
                        state["transactions"].insert(0, {
                            "address": address,
                            "hash": tx['transactionHash'],
                            "from": tx['from_address'],
                            "to": tx['to_address'],
                            "amount": float(tx['amount_str']) / 1e6,
                            "time": tx['block_ts']
                        })
                        state["transactions"] = state["transactions"][:20]
                        save_state(state)
        time.sleep(state["check_interval"])

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form['username'] == USERNAME and request.form['password'] == PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        return "登录失败"
    return '''
        <form method="post">
            用户名：<input type="text" name="username"><br>
            密码：<input type="password" name="password"><br>
            <input type="submit" value="登录">
        </form>
    '''

@app.before_request
def require_login():
    if request.endpoint not in ('login', 'static') and not session.get('logged_in'):
        return redirect("/login")

@app.route("/")
def index():
    state = load_state()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return render_template("index.html", state=state, now=now)

@app.route("/toggle")
def toggle():
    state = load_state()
    state["is_running"] = not state["is_running"]
    save_state(state)
    return redirect("/")

@app.route("/addresses", methods=["GET", "POST"])
def addresses():
    state = load_state()
    if request.method == "POST":
        addr = request.form.get("address")
        if addr and addr not in state["watch_addresses"]:
            state["watch_addresses"].append(addr)
            save_state(state)
    return render_template("addresses.html", state=state)

@app.route("/addresses/delete/<addr>")
def delete_address(addr):
    state = load_state()
    state["watch_addresses"] = [a for a in state["watch_addresses"] if a != addr]
    save_state(state)
    return redirect("/addresses")

if __name__ == "__main__":
    Thread(target=monitor_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=8888)



@app.route("/chart")
def chart():
    from collections import defaultdict
    from datetime import datetime

    state = load_state()
    txs = state.get("transactions", [])

    start_str = request.args.get("start")
    end_str = request.args.get("end")
    mode = request.args.get("mode", "date")
    direction = request.args.get("direction", "all")

    fmt = "%Y-%m-%d"
    if start_str:
        start_date = datetime.strptime(start_str, fmt)
    else:
        start_date = datetime.utcfromtimestamp(0)
        start_str = ""
    if end_str:
        end_date = datetime.strptime(end_str, fmt)
    else:
        end_date = datetime.now()
        end_str = ""

    data = defaultdict(float)
    for tx in txs:
        ts = int(tx["time"]) // 1000
        tx_date = datetime.fromtimestamp(ts)
        if not (start_date <= tx_date <= end_date):
            continue

        addr = tx["address"]
        to_addr = tx["to"]
        from_addr = tx["from"]
        is_out = addr == from_addr
        is_in = addr == to_addr

        if direction == "in" and not is_in:
            continue
        if direction == "out" and not is_out:
            continue

        key = tx_date.strftime(fmt) if mode == "date" else addr
        data[key] += tx["amount"]

    sorted_keys = sorted(data.keys())
    values = [round(data[k], 2) for k in sorted_keys]
    return render_template("chart.html",
                           labels=sorted_keys,
                           values=values,
                           mode=mode,
                           direction=direction,
                           start=start_str,
                           end=end_str,
                           label="USDT - " + ("收入" if direction == "in" else "支出" if direction == "out" else "全部"))
