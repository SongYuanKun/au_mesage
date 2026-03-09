import logging
import os

from mysql_manager import MySQLManager
from playwright_collector import PlaywrightDataCollector
from route import create_app


def setup_logging():
    """配置日志系统"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('../price_service.log'),
            logging.StreamHandler()
        ]
    )


def load_config():
    """从环境变量加载配置"""
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
    """主程序入口"""
    # 初始化和配置
    setup_logging()
    config = load_config()

    # 初始化MySQL管理器
    mysql_manager = MySQLManager(config['mysql'])

    # 初始化Playwright数据采集器
    data_collector = PlaywrightDataCollector(mysql_manager)

    # 启动数据采集服务
    data_collector.start_collection()
    logging.info("Playwright数据采集服务已启动")

    # 创建并启动Flask应用
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
        data_collector.stop_collection()
        logging.info("服务已安全退出")


if __name__ == "__main__":
    main()