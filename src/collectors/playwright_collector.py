"""
PlaywrightCollector — 通过 Playwright 抓取金紫荆网站国内零售价
可选采集器，通过 ENABLE_PLAYWRIGHT=true 启用
"""
import logging
import os
import threading
import time
from datetime import datetime

import pytz
from playwright.sync_api import sync_playwright

from collectors import stats as collector_stats
from collectors.base import BaseCollector

logger = logging.getLogger(__name__)
BEIJING_TZ = pytz.timezone('Asia/Shanghai')
ROW_SELECTOR = '.quote-price-table .price-table-row'


class PlaywrightCollector(BaseCollector):
    name = 'playwright'
    interval = 60
    # 浏览器会话失效后的重建退避（秒），指数增长到上限
    restart_delay = 30
    max_restart_delay = 600
    # 页面仍在但连续采集失败达到该次数，也重建会话
    max_session_failures = 3
    retry_delay = 30

    def __init__(self, mysql_manager):
        super().__init__(mysql_manager)
        self.website_url = os.environ.get('WEBSITE_URL', 'https://i.jzj9999.com/quoteh5/')
        self.data_buffer = []
        self.data_lock = threading.Lock()
        self.browser = None
        self.page = None
        self._save_thread = None
        self._stop_event = threading.Event()

    def start(self):
        """Playwright 需要独立线程管理浏览器生命周期，覆盖父类 start"""
        if self.is_running:
            return
        if any(t is not None and t.is_alive() for t in (self._thread, self._save_thread)):
            raise RuntimeError(f"[{self.name}] 上一个采集线程仍在运行")
        self._stop_event = threading.Event()
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
        restarts = 0
        try:
            while self.is_running:
                had_success = False
                try:
                    with sync_playwright() as p:
                        had_success = self._run_session(p)
                except Exception as e:
                    collector_stats.record_failure(self.name)
                    logger.error(f"[playwright] 浏览器会话异常: {e}")
                if not self.is_running:
                    break
                # 会话内采集成功过就从最短退避重来；一直失败则指数退避，避免目标站故障时频繁拉起浏览器
                restarts = 1 if had_success else restarts + 1
                delay = self._restart_delay_for(restarts)
                logger.warning(f"[playwright] {delay}s 后重建浏览器会话（连续第 {restarts} 次）")
                self._stop_event.wait(delay)
        finally:
            # 线程退出即视为停止，管理器会按配置重新拉起
            self.is_running = False
            self._stop_event.set()

    def _restart_delay_for(self, restarts: int) -> float:
        return min(self.max_restart_delay, self.restart_delay * 2 ** (restarts - 1))

    def _run_session(self, p) -> bool:
        """启动浏览器并循环采集；浏览器/页面失效或连续失败时返回，由外层重建。返回本会话是否采集成功过。"""
        had_success = False
        browser = p.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled',
                  '--disable-dev-shm-usage', '--no-sandbox']
        )
        self.browser = browser
        try:
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            self.page = context.new_page()
            self.page.set_default_timeout(30000)
            # SPA 长时间长连时 networkidle 可能永不触发，改用 domcontentloaded + 等待表格
            self.page.goto(self.website_url, wait_until='domcontentloaded')
            self.page.wait_for_selector(ROW_SELECTOR, timeout=30000)
            logger.info("[playwright] 浏览器初始化完成，开始监控数据...")

            failures = 0
            while self.is_running:
                started = time.monotonic()
                try:
                    data = self._refresh_and_get_data()
                    if not data:
                        raise RuntimeError("页面未解析到任何报价")
                except Exception as e:
                    failures += 1
                    collector_stats.record_failure(self.name)
                    logger.error(f"[playwright] 采集失败 (连续 {failures} 次): {e}")
                    if self._session_broken(browser) or failures >= self.max_session_failures:
                        return had_success
                    self._stop_event.wait(self.retry_delay)
                    continue

                failures = 0
                had_success = True
                collector_stats.record_success(self.name, (time.monotonic() - started) * 1000.0)
                with self.data_lock:
                    self.data_buffer.extend(data)
                    buffered = len(self.data_buffer)
                logger.info(f"[playwright] 获取 {len(data)} 条数据，缓冲区 {buffered} 条")
                self._stop_event.wait(self.interval)
            return had_success
        finally:
            # 浏览器只能在创建它的线程里关闭
            self.page = None
            self.browser = None
            try:
                browser.close()
            except Exception as e:
                logger.warning(f"[playwright] 关闭浏览器失败: {e}")

    def _session_broken(self, browser) -> bool:
        """浏览器断开或页面已关闭（如 Target page, context or browser has been closed）时需要重建。"""
        try:
            return not browser.is_connected() or self.page is None or self.page.is_closed()
        except Exception:
            return True

    def _refresh_and_get_data(self) -> list:
        """刷新页面并解析报价；页面级异常向上抛出，由调用方决定重试或重建会话。"""
        self.page.reload(wait_until='domcontentloaded')
        self.page.wait_for_selector(ROW_SELECTOR, timeout=15000)
        elements = self.page.query_selector_all(ROW_SELECTOR)
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

    def _save_job(self):
        while self.is_running:
            self._stop_event.wait(30)
            to_store = []
            with self.data_lock:
                if self.data_buffer:
                    to_store = self.data_buffer.copy()
                    self.data_buffer = []
            
            if to_store:
                try:
                    self.mysql_manager.batch_insert_data(to_store)
                    logger.info(f"[playwright] 存储 {len(to_store)} 条数据")
                except Exception as e:
                    logger.error(f"[playwright] 存储错误: {e}")
                    # 如果存储失败，考虑把数据加回去，但要注意顺序或重复
                    with self.data_lock:
                        self.data_buffer = to_store + self.data_buffer

    def stop(self, join_timeout: float = 20.0):
        # 只发停止信号并等待两个线程退出，浏览器由采集线程自行关闭
        self.is_running = False
        self._stop_event.set()
        for thread in (self._thread, self._save_thread):
            if thread is None:
                continue
            if thread is threading.current_thread():
                raise RuntimeError(f"[{self.name}] 采集线程不能等待自身退出")
            thread.join(timeout=join_timeout)
            if thread.is_alive():
                raise RuntimeError(f"[{self.name}] 采集线程未在 {join_timeout}s 内退出")
        self._thread = None
        self._save_thread = None
        logger.info("[playwright] 已停止")
