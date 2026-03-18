"""
多通道价格提醒推送模块
支持：企业微信机器人、Telegram Bot、邮件

配置通过环境变量：
  WECHAT_WEBHOOK_URL   - 企业微信机器人 Webhook 地址
  TELEGRAM_BOT_TOKEN   - Telegram Bot Token
  TELEGRAM_CHAT_ID     - Telegram 接收消息的 Chat ID
  SMTP_HOST            - 邮件 SMTP 服务器
  SMTP_PORT            - SMTP 端口 (默认 465)
  SMTP_USER            - SMTP 用户名
  SMTP_PASS            - SMTP 密码
  ALERT_EMAIL_TO       - 接收提醒的邮箱地址
"""

import logging
import os
import json
import smtplib
from email.mime.text import MIMEText
from urllib.request import Request, urlopen
from urllib.error import URLError

logger = logging.getLogger(__name__)


def _post_json(url, payload, timeout=10):
    """发送 JSON POST 请求（使用标准库，不依赖 requests）"""
    data = json.dumps(payload).encode('utf-8')
    req = Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        resp = urlopen(req, timeout=timeout)
        return resp.status == 200
    except (URLError, Exception) as e:
        logger.error(f"POST 请求失败 ({url}): {e}")
        return False


def send_wechat(title, content):
    """企业微信机器人推送"""
    url = os.environ.get('WECHAT_WEBHOOK_URL')
    if not url:
        return False
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "content": f"### {title}\n{content}"
        }
    }
    return _post_json(url, payload)


def send_telegram(title, content):
    """Telegram Bot 推送"""
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    if not token or not chat_id:
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": f"*{title}*\n{content}",
        "parse_mode": "Markdown"
    }
    return _post_json(url, payload)


def send_email(title, content):
    """邮件推送"""
    host = os.environ.get('SMTP_HOST')
    user = os.environ.get('SMTP_USER')
    passwd = os.environ.get('SMTP_PASS')
    to_addr = os.environ.get('ALERT_EMAIL_TO')
    if not all([host, user, passwd, to_addr]):
        return False
    port = int(os.environ.get('SMTP_PORT', '465'))
    msg = MIMEText(content, 'plain', 'utf-8')
    msg['Subject'] = title
    msg['From'] = user
    msg['To'] = to_addr
    try:
        with smtplib.SMTP_SSL(host, port) as smtp:
            smtp.login(user, passwd)
            smtp.sendmail(user, [to_addr], msg.as_string())
        return True
    except Exception as e:
        logger.error(f"邮件发送失败: {e}")
        return False


def notify_all(title, content):
    """向所有已配置的渠道推送通知，返回成功的渠道列表"""
    channels = [
        ('wechat', send_wechat),
        ('telegram', send_telegram),
        ('email', send_email),
    ]
    sent = []
    for name, fn in channels:
        try:
            if fn(title, content):
                sent.append(name)
                logger.info(f"通知发送成功: {name}")
        except Exception as e:
            logger.error(f"通知发送异常 ({name}): {e}")
    return sent


def get_configured_channels():
    """返回已配置的推送渠道列表"""
    channels = []
    if os.environ.get('WECHAT_WEBHOOK_URL'):
        channels.append('wechat')
    if os.environ.get('TELEGRAM_BOT_TOKEN') and os.environ.get('TELEGRAM_CHAT_ID'):
        channels.append('telegram')
    if os.environ.get('SMTP_HOST') and os.environ.get('SMTP_USER'):
        channels.append('email')
    return channels
