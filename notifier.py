
import smtplib
from email.mime.text import MIMEText
import requests
import os

def send_telegram(msg):
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {'chat_id': chat_id, 'text': msg}
    requests.post(url, data=payload)

def send_email(msg):
    sender = os.getenv('EMAIL_SENDER')
    password = os.getenv('EMAIL_PASSWORD')
    receiver = os.getenv('EMAIL_RECEIVER')
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = int(os.getenv('SMTP_PORT', 587))

    mime = MIMEText(msg, 'plain', 'utf-8')
    mime['Subject'] = 'USDT 转账通知'
    mime['From'] = sender
    mime['To'] = receiver

    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(sender, password)
    server.sendmail(sender, receiver, mime.as_string())
    server.quit()
