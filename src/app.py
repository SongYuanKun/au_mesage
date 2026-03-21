import logging
import os
import sys

# collectors 目录与 app.py 同在 src/，确保可导入
sys.path.insert(0, os.path.dirname(__file__))

from mysql_manager import MySQLManager
from collectors.manager import CollectorManager
from route import create_app


def setup_logging():
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    log_dir = os.path.join(base, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, 'price_service.log')
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler()
        ]
    )


def load_config():
    return {
        'mysql': {
            'host': os.environ.get('MYSQL_HOST', 'localhost'),
            'user': os.environ.get('MYSQL_USER', 'root'),
            'password': os.environ['MYSQL_PASSWORD'],
            'database': os.environ.get('MYSQL_DATABASE', 'price_data')
        },
        'api': {
            'host': os.environ.get('API_HOST', '0.0.0.0'),
            'port': int(os.environ.get('API_PORT', '8083'))
        }
    }


def main():
    setup_logging()
    config = load_config()

    mysql_manager = MySQLManager(config['mysql'])

    collector_manager = CollectorManager(mysql_manager)
    collector_manager.start_all()

    app = create_app(mysql_manager)

    try:
        app.run(
            host=config['api']['host'],
            port=config['api']['port'],
            debug=False,
            use_reloader=False
        )
    except KeyboardInterrupt:
        logging.info("收到停止信号，正在关闭服务...")
    finally:
        collector_manager.stop_all()
        logging.info("服务已安全退出")


if __name__ == "__main__":
    main()
