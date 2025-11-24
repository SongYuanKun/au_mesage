import logging
import threading
import time
from datetime import datetime

from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)


class PlaywrightDataCollector:
    def __init__(self, mysql_manager):
        self.mysql_manager = mysql_manager
        self.data_buffer = []
        self.is_running = False
        self.browser = None
        self.page = None
        self.website_url = "https://your_website_url.com"  

    def start_collection(self):
        """启动数据采集服务"""
        self.is_running = True

        # 启动Playwright采集线程
        collection_thread = threading.Thread(target=self._run_playwright)
        collection_thread.daemon = True
        collection_thread.start()

        # 启动定时存储任务
        storage_thread = threading.Thread(target=self._save_job)
        storage_thread.daemon = True
        storage_thread.start()

        logger.info("数据采集服务已启动")

    def _run_playwright(self):
        """运行Playwright浏览器实例"""
        try:
            with sync_playwright() as p:
                # 启动浏览器（无头模式可改为False用于调试）
                self.browser = p.chromium.launch(
                    headless=True,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--no-sandbox'
                    ]
                )

                # 创建浏览上下文
                context = self.browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )

                self.page = context.new_page()

                # 设置超时时间
                self.page.set_default_timeout(30000)

                # 访问目标网站
                self.page.goto(self.website_url)
                self.page.wait_for_load_state('networkidle')

                logger.info("浏览器初始化完成，开始监控数据...")

                # 主循环
                while self.is_running:
                    try:
                        # 定期刷新并获取数据
                        data = self._refresh_and_get_data()
                        if data:
                            self.data_buffer.extend(data)
                            logger.info(f"获取到 {len(data)} 条新数据，缓冲区共有 {len(self.data_buffer)} 条数据")

                        # 等待一段时间后再次刷新
                        time.sleep(60)  # 每分钟刷新一次

                    except Exception as loop_error:
                        logger.error(f"数据采集循环错误: {loop_error}")
                        time.sleep(30)  # 出错时等待30秒后重试

        except Exception as e:
            logger.error(f"Playwright运行错误: {e}")
        finally:
            if self.browser:
                self.browser.close()

    def _refresh_and_get_data(self):
        """刷新页面并获取表格数据"""
        try:
            # 刷新页面并等待加载完成
            self.page.reload()
            self.page.wait_for_load_state('networkidle')

            # 等待表格加载
            self.page.wait_for_selector('.quote-price-table .price-table-row', timeout=10000)

            # 获取所有价格表格行元素
            data_elements = self.page.query_selector_all('.quote-price-table .price-table-row')
            extracted_data = []

            for element in data_elements:
                try:
                    # 提取商品名称
                    product_name_elem = element.query_selector('.symbol-name')
                    product_name = product_name_elem.inner_text().strip() if product_name_elem else "未知商品"
                    # 提取回购价格（第二列）
                    buyback_price_elem = element.query_selector(
                        '.el-col-6:nth-child(2) .symbol-price-rise, .el-col-6:nth-child(2) .symbol-price-fall, .el-col-6:nth-child(2) .symbole-price span'
                    )
                    buyback_price = buyback_price_elem.inner_text().strip() if buyback_price_elem else "0"

                    # 提取销售价格（第三列）
                    selling_price_elem = element.query_selector(
                        '.el-col-6:nth-child(3) .symbol-price-rise, .el-col-6:nth-child(3) .symbol-price-fall, .el-col-6:nth-child(3) .symbole-price span'
                    )
                    selling_price = selling_price_elem.inner_text().strip() if selling_price_elem else "0"

                    # 提取高价（第四列第一个值）
                    high_price_elem = element.query_selector(
                        '.el-col-6:nth-child(4) .symbol-price-rise:nth-child(1), .el-col-6:nth-child(4) .symbol-price-fall:nth-child(1), .el-col-6:nth-child(4) .symbole-price span:nth-child(1)')
                    high_price = high_price_elem.inner_text().strip() if high_price_elem else "0"

                    # 提取低价（第四列第二个值）
                    low_price_elem = element.query_selector(
                        '.el-col-6:nth-child(4) .symbol-price-rise:nth-child(2), .el-col-6:nth-child(4) .symbol-price-fall:nth-child(2), .el-col-6:nth-child(4) .symbole-price span:nth-child(2)')
                    low_price = low_price_elem.inner_text().strip() if low_price_elem else "0"

                    # 清理价格数据
                    def clean_price(price_str):
                        if price_str in ['--', '']:
                            return '0'
                        cleaned = ''.join(ch for ch in price_str if ch.isdigit() or ch in '.-')
                        return cleaned if cleaned else '0'

                    buyback_price = clean_price(buyback_price)
                    selling_price = clean_price(selling_price)
                    high_price = clean_price(high_price)
                    low_price = clean_price(low_price)

                    # 获取当前日期和时间
                    current_date = datetime.now().strftime('%Y-%m-%d')
                    current_time = datetime.now().strftime('%H:%M:%S')

                    data_item = {
                        'trade_date': current_date,
                        'trade_time': current_time,
                        'data_type': product_name,
                        'real_time_price': float(selling_price) if selling_price != '0' else 0.0,
                        'recycle_price': float(buyback_price) if buyback_price != '0' else 0.0,
                        'high_price': float(high_price) if high_price != '0' else 0.0,
                        'low_price': float(low_price) if low_price != '0' else 0.0
                    }

                    extracted_data.append(data_item)
                    logger.debug(f"提取数据: {product_name} - 回购: {buyback_price}, 销售: {selling_price}")

                except Exception as row_error:
                    logger.error(f"解析行数据时出错: {row_error}")
                    continue

            return extracted_data

        except Exception as e:
            logger.error(f"页面刷新或数据解析错误: {e}")
            return []

    def _save_job(self):
        """定时将缓冲数据存储到数据库"""
        while self.is_running:
            time.sleep(30)  # 每30秒检查一次

            if self.data_buffer:
                try:
                    # 复制当前缓冲区数据
                    data_to_store = self.data_buffer.copy()

                    # 存储到数据库
                    self.mysql_manager.batch_insert_data(data_to_store)

                    # 清空已存储的数据
                    self.data_buffer = []

                    logger.info(f"成功存储 {len(data_to_store)} 条数据到数据库")

                except Exception as storage_error:
                    logger.error(f"数据存储错误: {storage_error}")

    def stop_collection(self):
        """停止数据采集"""
        self.is_running = False
        if self.browser:
            self.browser.close()
        logger.info("数据采集服务已停止")