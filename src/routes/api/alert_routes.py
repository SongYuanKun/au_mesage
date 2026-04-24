"""价格提醒：主动推送与 SSE。"""

from __future__ import annotations

import json
import logging
import time

from flask import Blueprint, Response, jsonify, request, stream_with_context

from db import DatabaseManager


def register_alert_routes(bp: Blueprint, mysql_manager: DatabaseManager) -> None:
    @bp.route("/api/alert-channels", methods=["GET"])
    def alert_channels():
        """返回已配置的推送渠道"""
        from webhook_notifier import get_configured_channels

        return jsonify({"success": True, "channels": get_configured_channels()})

    @bp.route("/api/price-alert/push", methods=["POST"])
    def price_alert_push():
        """
        增强版价格提醒：支持多通道推送。
        请求体: { data_type, target, op: 'gte'|'lte', channels: ['wechat','telegram','email'] }
        """
        try:
            data = request.get_json()
            data_type = data.get("data_type")
            target = data.get("target")
            op = data.get("op", "gte")
            channels = data.get("channels", [])

            if not data_type or target is None:
                return jsonify({"success": False, "error": "缺少参数: data_type 或 target"}), 400
            target = float(target)

            price = mysql_manager.get_latest_market_price(data_type)
            if price is None:
                return jsonify({"success": False, "error": "无法获取最新价格"}), 404

            price_f = float(price)
            triggered = (op == "gte" and price_f >= target) or (op == "lte" and price_f <= target)

            result = {
                "success": True,
                "current_price": price_f,
                "target": target,
                "op": op,
                "triggered": triggered,
                "sent_channels": [],
            }

            if triggered and channels:
                from webhook_notifier import send_email, send_telegram, send_wechat

                op_text = "达到或超过" if op == "gte" else "达到或低于"
                title = f"{data_type}价格提醒"
                content = f"当前价格 {price_f} 元/克，已{op_text}目标价 {target} 元/克"

                channel_fns = {"wechat": send_wechat, "telegram": send_telegram, "email": send_email}
                sent = []
                for ch in channels:
                    fn = channel_fns.get(ch)
                    if fn:
                        try:
                            if fn(title, content):
                                sent.append(ch)
                        except Exception as e:
                            logging.error(f"推送失败 ({ch}): {e}")
                result["sent_channels"] = sent

            return jsonify(result)
        except Exception as e:
            logging.error(f"价格提醒推送错误: {e}")
            return jsonify({"success": False, "error": "服务器内部错误"}), 500

    @bp.route("/api/price-alert/subscribe", methods=["GET"])
    def price_alert_subscribe():
        data_type = request.args.get("data_type")
        target_raw = request.args.get("target")
        op = request.args.get("op", "gte")
        auto_close = request.args.get("auto_close", "true").lower() == "true"
        try:
            if not data_type or target_raw is None:
                return jsonify({"success": False, "error": "缺少参数: data_type 或 target"}), 400
            target = float(target_raw)
        except Exception:
            return jsonify({"success": False, "error": "参数格式错误"}), 400

        def sse_stream():
            alerted = False
            start_time = time.time()
            timeout_seconds = 30 * 60  # 30分钟超时
            while True:
                # 超时检查
                if time.time() - start_time > timeout_seconds:
                    yield "event: timeout\n"
                    yield "data: 订阅超时，请重新订阅\n\n"
                    break

                price = mysql_manager.get_latest_market_price(data_type)
                if price is None:
                    yield "event: error\n"
                    yield "data: 无法获取最新市场价格\n\n"
                    break
                payload_price = json.dumps({"price": float(price)})
                yield "event: price\n"
                yield f"data: {payload_price}\n\n"
                cond = (op == "gte" and float(price) >= target) or (op == "lte" and float(price) <= target)
                if cond and not alerted:
                    payload_alert = json.dumps({"price": float(price), "target": target, "op": op})
                    yield "event: alert\n"
                    yield f"data: {payload_alert}\n\n"
                    alerted = True
                    try:
                        from webhook_notifier import notify_all

                        op_text = "达到或超过" if op == "gte" else "达到或低于"
                        notify_all(
                            f"{data_type}价格提醒",
                            f"当前价格 {float(price)} 元/克，已{op_text}目标价 {target} 元/克",
                        )
                    except Exception:
                        pass
                    if auto_close:
                        break
                yield "event: ping\n"
                yield "data: keepalive\n\n"
                time.sleep(5)

        headers = {"Cache-Control": "no-cache", "Connection": "keep-alive"}
        return Response(stream_with_context(sse_stream()), mimetype="text/event-stream", headers=headers)
