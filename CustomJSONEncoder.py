from flask import Flask
from flask.json.provider import DefaultJSONProvider
from datetime import datetime, date, timedelta
from decimal import Decimal


class CustomJSONProvider(DefaultJSONProvider):
    def default(self, obj):
        # 处理 timedelta 对象，转换为总秒数
        if isinstance(obj, timedelta):
            return obj.total_seconds()

        # 处理 datetime 对象，格式化为 YYYY-MM-DD hh:mm:ss
        elif isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")

        # 处理 date 对象，格式化为 YYYY-MM-DD
        elif isinstance(obj, date):
            return obj.strftime("%Y-%m-%d")

        # 处理 Decimal 类型，转换为浮点数
        elif isinstance(obj, Decimal):
            return float(obj)

        # 对于其他类型，调用父类默认处理
        return super().default(obj)


# 应用配置示例
app = Flask(__name__)
app.json = CustomJSONProvider(app)