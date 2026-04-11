"""
PlaywrightCollector — 通过 Playwright 抓取金紫荆网站国内零售价
可选采集器，通过 ENABLE_PLAYWRIGHT=true 启用
"""
import logging
import os
import time
from datetime import datetime

import pytz
from playwright.sync_api import sync_playwright

from collectors.base import BaseCollector

logger = logging.getLogger(__name__)
BEIJING_TZ = pytz.timezone('Asia/Shanghai')


class PlaywrightCollector(BaseCollector):
    name = 'playwright'
    interval = 60

    def __init__(self, mysql_manager):
        super().__init__(mysql_manager)
        self.website_url = os.environ.get('WEBSITE_URL', 'https://i.jzj9999.com/quoteh5/')
        self.data_buffer = []
        self.browser = None
        self.page = None

    def start(self):
        """Playwright 需要独立线程管理浏览器生命周期，覆盖父类 start"""
        import threading
        self.is_running = True
        self._thread = threading.Thread(target=self._run_playwright, daemon=True)
        self._thread.start()
        self._save_thread = threading.Thread(target=self._save_job, daemon=True)
        self._save_thread.start()
        logger.info(f"[{self.name}] Playwright 采集器已启动")

    def fetch(self) -> list:
        """由 _run_playwright 直接调用，此方法仅供接口兼容"""
        return self._refresh_and_get_data()

    def _run_playwright(self):
        try:
            with sync_playwright() as p:
                self.browser = p.chromium.launch(
                    headless=True,
                    args=['--disable-blink-features=AutomationControlled',
                          '--disable-dev-shm-usage', '--no-sandbox']
                )
                context = self.browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                self.page = context.new_page()
                self.page.set_default_timeout(30000)
                # SPA 长时间长连时 networkidle 可能永不触发，改用 domcontentloaded + 等待表格
                self.page.goto(self.website_url, wait_until='domcontentloaded')
                self.page.wait_for_selector('.quote-price-table .price-table-row', timeout=30000)
                logger.info("[playwright] 浏览器初始化完成，开始监控数据...")

                while self.is_running:
                    try:
                        data = self._refresh_and_get_data()
                        if data:
                            self.data_buffer.extend(data)
                            logger.info(f"[playwright] 获取 {len(data)} 条数据，缓冲区 {len(self.data_buffer)} 条")
                        time.sleep(self.interval)
                    except Exception as e:
                        logger.error(f"[playwright] 采集循环错误: {e}")
                        time.sleep(30)
        except Exception as e:
            logger.error(f"[playwright] 运行错误: {e}")
        finally:
            if self.browser:
                self.browser.close()

    def _refresh_and_get_data(self) -> list:
        try:
            self.page.reload(wait_until='domcontentloaded')
            self.page.wait_for_selector('.quote-price-table .price-table-row', timeout=15000)
            elements = self.page.query_selector_all('.quote-price-table .price-table-row')
            extracted = []

            for element in elements:
                try:
                    # 行结构：el-col-8 品名 + 三个 el-col-6（回购/销售/最高+现价等，第四列可能含两个价）
                    name_el = element.query_selector('.symbol-name')
                    product_name = name_el.inner_text().strip() if name_el else '未知商品'

                    def get_price(nth):
                        # nth 为 el-row 下第 n 个子节点；第 1 列为 el-col-8，价从第 2 列起为 el-col-6
                        el = element.query_selector(
                            f'.el-col-6:nth-child({nth}) .symbol-price-rise,'
                            f'.el-col-6:nth-child({nth}) .symbol-price-fall,'
                            f'.el-col-6:nth-child({nth}) .symbole-price span'
                        )
                        raw = el.inner_text().strip() if el else '0'
                        cleaned = ''.join(c for c in raw if c.isdigit() or c in '.-')
                        return float(cleaned) if cleaned else 0.0

                    # 与页面列顺序一致：回购、销售、最高（第四列多价时取首个匹配，一般为最高价）
                    buyback = get_price(2)
                    selling = get_price(3)
                    high = get_price(4)

                    beijing_now = datetime.now(BEIJING_TZ)
                    extracted.append({
                        'trade_date': beijing_now.strftime('%Y-%m-%d'),
                        'trade_time': beijing_now.strftime('%H:%M:%S'),
                        'data_type': product_name,
                        'real_time_price': selling,
                        'recycle_price': buyback,
                        'high_price': high,
                        'low_price': 0,
                        'source': self.name,
                        'currency': 'CNY',
                    })
                except Exception as e:
                    logger.error(f"[playwright] 解析行错误: {e}")

            return extracted
        except Exception as e:
            logger.error(f"[playwright] 页面刷新错误: {e}")
            return []

    def _save_job(self):
        while self.is_running:
            time.sleep(30)
            if self.data_buffer:
                try:
                    to_store = self.data_buffer.copy()
                    self.mysql_manager.batch_insert_data(to_store)
                    self.data_buffer = []
                    logger.info(f"[playwright] 存储 {len(to_store)} 条数据")
                except Exception as e:
                    logger.error(f"[playwright] 存储错误: {e}")

    def stop(self):
        self.is_running = False
        if self.browser:
            self.browser.close()
        logger.info("[playwright] 已停止")
