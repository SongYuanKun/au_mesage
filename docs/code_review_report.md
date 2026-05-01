# AU 贵金属价格采集与分析平台 - 代码审查报告

## 1. 执行摘要
本次审查对现有代码库进行了全面的逻辑、安全、性能及可维护性分析。项目后端架构稳健，模块化程度高，但在安全性配置、数据采集并发性、数据库查询效率以及前端基础实现方面存在若干关键问题。

## 2. 问题清单与风险评估

### 2.1 安全漏洞 (Security)
| 编号 | 问题描述 | 风险等级 | 影响范围 | 建议修复方案 |
| :--- | :--- | :--- | :--- | :--- |
| SEC-01 | `my_config.ini` 中硬编码数据库凭据 | **高** | 全局 | 将凭据移至 `.env` 文件，并在 `.gitignore` 中忽略。 |
| SEC-02 | Docker 容器以 root 用户身份运行 | **中** | 部署安全 | 在 Dockerfile 中创建并切换至非 root 用户。 |
| SEC-03 | 模板中手动拼接 HTML 导致 XSS 风险 | **中** | `index.html`, `analysis.html` | 使用 `textContent` 或模板引擎转义功能。 |
| SEC-04 | API 输入验证不足（如 `float()` 转换） | **中** | `alert_routes.py`, `price_routes.py` | 使用 `pydantic` 或 `try-except` 捕获转换异常并返回 400。 |
| SEC-05 | 生产构建中包含开发工具 (`react-dev-locator`) | **低** | 前端构建 | 优化 `vite.config.ts` 逻辑，仅在开发环境加载。 |

### 2.2 性能瓶颈 (Performance)
| 编号 | 问题描述 | 影响等级 | 影响范围 | 建议修复方案 |
| :--- | :--- | :--- | :--- | :--- |
| PER-01 | 实时在 `price_data` 表上进行 OHLC 窗口计算 | **高** | 趋势分析 API | 优先使用 `daily_ohlc` 汇总表，仅当日数据回溯明细表。 |
| PER-02 | 采集器顺序执行网络请求 | **中** | `GoldAPICollector` | 引入 `ThreadPoolExecutor` 或 `asyncio` 并行抓取。 |
| PER-03 | 数据库连接池容量过小 (pool_size=5) | **中** | 数据库访问层 | 将连接池大小配置化，并适当调大至 15-20。 |
| PER-04 | Playwright 跨进程 DOM 遍历效率低 | **低** | `PlaywrightCollector` | 使用 `page.evaluate()` 在浏览器侧一次性提取数据。 |

### 2.3 逻辑错误与稳定性 (Logic & Stability)
| 编号 | 问题描述 | 严重程度 | 影响范围 | 建议修复方案 |
| :--- | :--- | :--- | :--- | :--- |
| LOG-01 | `PlaywrightCollector` 缓冲区清空存在竞态条件 | **高** | 数据采集 | 使用 `threading.Lock` 或 `queue.Queue` 确保线程安全。 |
| LOG-02 | 价格差计算未处理 `market_price` 为 0 的情况 | **低** | `calculations.py` | 增加除零检查，返回 `None` 或错误提示。 |
| LOG-03 | 硬编码的金属品种名称 | **低** | `TrendReader` | 统一品种命名规范或使用配置映射表。 |

### 2.4 编码规范与可维护性 (Maintainability)
| 编号 | 问题描述 | 类别 | 建议修复方案 |
| :--- | :--- | :--- | :--- |
| MNT-01 | 数据库访问层存在大量重复的连接管理代码 | 代码冗余 | 引入上下文管理器或装饰器抽象 DB 连接逻辑。 |
| MNT-02 | `app.py` 中使用 `sys.path.insert` 修改导入路径 | 架构设计 | 优化项目安装方式或设置 `PYTHONPATH` 环境变量。 |
| MNT-03 | `README.md` 内容缺失（仍为 Vite 默认模板） | 文档完整性 | 补全项目说明、启动指南和 API 文档。 |
| MNT-04 | `requirements.txt` 缺失部分包的版本号 | 依赖管理 | 明确锁定包版本，防止环境不一致。 |

## 3. 代码重构方案

### 3.1 数据库层重构 (DRY 原则)
在 `src/db/pool.py` 中增加连接管理上下文：
```python
@contextmanager
def get_cursor(self):
    conn = self.pool.get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        yield cursor
        conn.commit()
    finally:
        cursor.close()
        conn.close()
```

### 3.2 采集器并发优化
将 `GoldAPICollector` 中的顺序循环改为线程池并发：
```python
with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(self._fetch_symbol, symbol) for symbol in symbols]
    # 处理结果...
```

### 3.3 输入验证层
引入 `pydantic` 模型对 API 输入进行校验，并建立全局错误处理机制。

## 4. 后续验证计划
1. **单元测试**：针对重构后的数据库层和计算逻辑编写 `pytest`。
2. **压力测试**：模拟高并发采集，验证连接池及采集器稳定性。
3. **回归测试**：确保重构不影响现有的 ECharts 图表展示和 SSE 实时推送功能。
