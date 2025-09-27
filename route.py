# route.py
import logging
from datetime import datetime

from flask import Flask, jsonify, request, render_template

from CustomJSONEncoder import CustomJSONProvider
from mysql_manager import MySQLManager

app = Flask(__name__)
app.json = CustomJSONProvider(app)
def create_app(mysql_manager: MySQLManager):

    # Step 1 & 2: Create a new route to render index.html
    @app.route('/', methods=['GET'])
    def index():
        """渲染主页"""
        return render_template('index.html')

    @app.route('/api/latest-price', methods=['GET'])
    def get_latest_price():
        """获取最新价格接口"""
        try:
            data_type = request.args.get('type')
            data = mysql_manager.get_latest_data(data_type)

            if data:
                return jsonify({'success': True, 'data': data})
            else:
                return jsonify({'success': False, 'error': '未找到数据'}), 404

        except Exception as e:
            logging.error(f"最新价格接口错误: {e}")
            return jsonify({'success': False, 'error': '服务器内部错误'}), 500

    @app.route('/api/health', methods=['GET'])
    def health_check():
        """服务健康检查接口"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'service': 'price-data-api'
        })

    return app