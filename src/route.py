# route.py
import logging
from datetime import datetime

from flask import Flask, jsonify, request, render_template

from CustomJSONEncoder import CustomJSONProvider
from mysql_manager import MySQLManager

app = Flask(__name__, template_folder='../templates')
app.json = CustomJSONProvider(app)  # Ensure CustomJSONProvider is used


def create_app(mysql_manager: MySQLManager):
    @app.route('/', methods=['GET'])
    def index():
        """渲染主页"""
        return render_template('index.html')

    @app.route('/api/latest-price', methods=['GET'])
    def get_latest_price():
        """获取最新价格接口"""
        try:
            data_type = request.args.get('data_type')
            if not data_type:
                # If no specific data_type is requested, return the latest for each type
                data = mysql_manager.get_latest_data_by_type()
                if data:
                    return jsonify({'success': True, 'data': data}) 
                else:
                    return jsonify({'success': False, 'error': '未找到任何数据'}), 404
            else:
                data = mysql_manager.get_latest_data(data_type)
                if data:
                    return jsonify({'success': True, 'data': data})
                else:
                    return jsonify({'success': False, 'error': f'未找到 {data_type} 的最新数据'}), 404

        except Exception as e:
            logging.error(f"最新价格接口错误: {e}")
            return jsonify({'success': False, 'error': '服务器内部错误'}), 500

    @app.route('/api/recent-history', methods=['GET'])
    def get_recent_price_history():
        """获取指定data_type的近期历史价格数据接口 (用于图表)"""
        try:
            data_type = request.args.get('data_type')
            if not data_type:
                return jsonify({'success': False, 'error': '缺少data_type参数'}), 400

            history_data = mysql_manager.get_price_history(data_type, limit=30)  # Limit to 30 data points for chart

            if history_data:
                return jsonify({'success': True, 'data': history_data})
            else:
                return jsonify({'success': False, 'error': f'未找到 {data_type} 的近期历史数据'}), 404
        except Exception as e:
            logging.error(f"近期历史价格接口错误: {e}")
            return jsonify({'success': False, 'error': '服务器内部错误'}), 500

    @app.route('/api/daily-history', methods=['GET'])
    def get_daily_history():
        """
        获取指定日期和data_type的所有历史数据接口。
        默认返回今天的所有数据。
        """
        try:
            date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
            data_type = request.args.get('data_type')  # Optional data_type filter

            history_data = mysql_manager.get_daily_history(date_str, data_type)

            if history_data:
                return jsonify({'success': True, 'date': date_str, 'data_type': data_type, 'data': history_data})
            else:
                return jsonify({'success': False, 'error': f'未找到 {date_str} 的历史数据'}), 404
        except Exception as e:
            logging.error(f"每日历史数据接口错误: {e}")
            return jsonify({'success': False, 'error': '服务器内部错误'}), 500

        @app.route('/history', methods=['GET'])
        def history_page():
            """渲染近七天回收价格趋势页面"""
            return render_template('history.html')

        @app.route('/api/last-7-days', methods=['GET'])
        def api_last_7_days():
            """返回指定 data_type 的近 7 天每日回收价格（按天取当日最后一条数据的 recycle_price）"""
            try:
                data_type = request.args.get('data_type')
                if not data_type:
                    return jsonify({'success': False, 'error': '缺少 data_type 参数'}), 400

                from datetime import datetime, timedelta
                results = []
                today = datetime.now().date()
                # 从 6 天前 到 今天，按日期顺序返回
                for i in range(6, -1, -1):
                    day = today - timedelta(days=i)
                    day_str = day.strftime('%Y-%m-%d')
                    day_records = mysql_manager.get_daily_history(day_str, data_type)
                    # 取当日最后一条记录作为当天回收价（如果存在）
                    if day_records:
                        last_rec = day_records[-1]
                        price = float(last_rec.get('recycle_price', 0) or 0)
                    else:
                        price = None

                    results.append({'date': day_str, 'recycle_price': price})

                return jsonify({'success': True, 'data': results})
            except Exception as e:
                logging.error(f"获取近7天回收价格失败: {e}")
                return jsonify({'success': False, 'error': '服务器内部错误'}), 500

    @app.route('/api/history', methods=['POST'])
    def history():
        try:
            data = request.get_json()
            product_price = data.get('product_price')
            weight = data.get('weight')
            data_type = data.get('data_type')

            if not all([product_price, weight, data_type]):
                return jsonify({'error': '缺少参数: product_price, weight, 或 data_type'}), 400

            if not isinstance(product_price, (int, float)) or not isinstance(weight, (int, float)) or weight <= 0:
                return jsonify({'error': 'product_price 和 weight 必须是有效数字，且 weight 必须大于0'}), 400

            market_price = mysql_manager.get_latest_market_price(data_type)

            if market_price is None:
                return jsonify({'error': f'无法获取 {data_type} 的最新市场价格'}), 404

            price_per_gram = product_price / weight
            difference = price_per_gram - market_price
            difference_percentage = (difference / market_price) * 100 if market_price != 0 else 0

            return jsonify({
                'price_per_gram': price_per_gram,
                'market_price': market_price,
                'difference': difference,
                'difference_percentage': difference_percentage
            })

        except Exception as e:
            logging.error(f"计算价格差异接口错误: {e}")
            return jsonify({'error': '服务器内部错误'}), 500

    @app.route('/api/calculate', methods=['POST'])
    def calculate_price_difference():
        """
        计算价格差异接口 - 使用 float 类型统一计算
        """
        try:
            data = request.get_json()
            product_price = float(data.get('product_price'))
            weight = float(data.get('weight'))
            data_type = data.get('data_type')
            calculation_type = data.get('calculation_type', 'purchase')

            if weight <= 0:
                return jsonify({'error': 'weight 必须大于0'}), 400

            market_data = mysql_manager.get_latest_data(data_type)
            if not market_data:
                return jsonify({'error': f'未找到 {data_type} 的最新市场价格'}), 404

            # 将 Decimal 转换为 float
            market_price = float(market_data['recycle_price'])
            price_per_gram = product_price / weight

            # 根据计算类型调整差异计算
            difference = price_per_gram - market_price
            message_prefix = "购买价格差"
            positive_message = "💡 比大盘价格贵"
            negative_message = "💡 比大盘价格便宜"

            difference_percentage = (abs(difference) / market_price) * 100 if market_price != 0 else 0

            return jsonify({
                'price_per_gram': round(price_per_gram, 4),
                'market_price': round(market_price, 4),
                'total_difference': round(difference*weight, 4),
                'difference': round(difference, 4),
                'difference_percentage': round(difference_percentage, 2),
                'message_prefix': message_prefix,
                'positive_message': positive_message,
                'negative_message': negative_message
            })

        except (ValueError, TypeError) as e:
            return jsonify({'error': '参数格式错误，请检查输入数据'}), 400
        except Exception as e:
            logging.error(f"计算价格差异接口错误: {e}")
            return jsonify({'error': '服务器内部错误'}), 500

    @app.route('/api/health', methods=['GET'])
    def health_check():
        """服务健康检查接口"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'service': 'price-data-api'
        })

    return app
