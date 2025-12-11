# Copilot 使用说明（项目专用）

下面是让 AI 编码助理立即上手本仓库的精华说明。请只基于代码可见内容做修改。

## 一眼看懂架构
- 服务由两部分组成：数据采集（`src/playwright_collector.py`）与 HTTP API（Flask，`src/app.py` + `src/route.py`）。
- 数据流：Playwright 抓取 -> 内存缓冲 `data_buffer` -> 周期性调用 `MySQLManager.batch_insert_data` 写入 MySQL 表 `price_data` -> Flask API 从 MySQL 读取并返回给前端（`templates/index.html`）。
- 配置：`config.ini`（MySQL / API / Playwright 设置）。Docker 镜像由 `Dockerfile` 构建，`docker-compose.yml` 提供简单服务定义。

## 关键文件与示例（引用）
- 入口与启动：[src/app.py](src/app.py)（`main()` 会启动采集器并 run Flask）。
- 路由与 API：[src/route.py](src/route.py)（重点接口：`/api/latest-price`, `/api/recent-history`, `/api/calculate`, `/api/health`, `/api/last-1-hour`, `/api/last-7-days`, `/api/price-alert/subscribe`）。
- 数据库层：[src/mysql_manager.py](src/mysql_manager.py)（使用 `mysql.connector.pooling.MySQLConnectionPool`，表名 `price_data`，常用字段：`trade_date, trade_time, data_type, real_time_price, recycle_price, created_at`）。
- 采集器：[src/playwright_collector.py](src/playwright_collector.py)（无头浏览器抓取、线程后台运行、每分钟刷新、每30秒保存缓冲区）。
- 自定义 JSON 编码：[src/CustomJSONEncoder.py](src/CustomJSONEncoder.py)（将 `datetime`/`date`/`timedelta`/`Decimal` 转为 JSON 友好类型，Flask app 在 `route.py` 中使用）。
- 前端示例：[templates/index.html](templates/index.html)（使用 `/api/*` 接口，ECharts、自动计算逻辑）。

## 运行与调试（必备命令）
- 本地开发（PowerShell）：
```
python -m venv .venv;
.\.venv\Scripts\Activate.ps1;
pip install -r requirements.txt
python src/app.py
```
- Playwright 注意：安装后需安装浏览器二进制。运行一次（在虚拟环境中）：
```
playwright install
playwright install chromium
```
- Docker（构建并运行）：
```
docker build -t my-au .;
docker run -p 8083:8083 --env-file .env my-au
```
- docker-compose：
```
docker-compose up --build
```

## 项目约定与常见模式（可用于自动化修改）
- 配置文件：`config.ini` 位于项目根，必须包含 `[mysql]` 和 `[api]` 段。AI 改动时优先在 `config.ini` 或环境变量里说明更改点。
- **本地配置**：`my_config.ini` 优先级高于 `config.ini`，用于本地开发敏感信息。[src/playwright_collector.py](src/playwright_collector.py) 中 `load_website_url()` 优先读取 `my_config.ini`。
- 相对路径假设：`route.py` 将模板目录设置为 `template_folder='../templates'`，因此项目以根目录（包含 `src/` 与 `templates/`）为工作目录运行。修改文件或运行脚本时请确保当前工作目录为仓库根。
- **时区约定**：所有时间戳使用北京时区（`Asia/Shanghai`），通过 `pytz.timezone('Asia/Shanghai')` 获取。`created_at` 为 MySQL 自动时间戳，数据查询时基于此列排序和过滤。
- 数据过滤：SQL 查询通常包含 `and recycle_price > 0`（过滤无效价格），在改写查询要保留该条件以避免返回占位/无效数据。
- JSON 输出：项目使用 `CustomJSONProvider` 将 `Decimal` 转 float 并格式化 `datetime`；在修改 API 返回时遵循现有格式以免前端解析失败。
- 异常处理：路由函数中有通用 try/except 并记录错误，新增接口时请复用现有错误响应结构（{success: False, error: msg} 或 {'error': msg}）。
- **前端多页面**：项目有 3 个页面：[templates/index.html](templates/index.html)（主页，含计算器和实时价格），[templates/history.html](templates/history.html)（近 7 天趋势和 30 分钟实时数据），两者共享 [templates/_nav.html](templates/_nav.html) 和 [static/css/main.css](static/css/main.css)。

## 数据库交互注意点
- 连接池初始化在 `MySQLManager._initialize_pool`，池名 `price_pool`、默认大小 5。不要在高频路径反复创建新池。
- 插入 API 使用 `executemany` 批量写入；对大批量数据修改时保留事务（commit/rollback）逻辑。

## Playwright / 容器特殊注意事项
- `playwright_collector.py` 内部以线程方式启动浏览器并持续抓取：停止服务通过 `data_collector.stop_collection()`（`KeyboardInterrupt` 路径已处理）。
- 在容器中运行时：确保已执行 `playwright install` 或在 Dockerfile 中安装浏览器二进制；容器运行时需要 `--no-sandbox` 等参数（代码中已设置）。
- 采集器默认 `headless=True`（文件顶部 `website_url` 和选择器由页面结构决定），如需调试将其临时改为 `headless=False` 并在本地运行。

## 数据库初始化（必须在首次运行前执行）
运行以下 SQL 在 MySQL 中创建价格数据表（使用 `config.ini` 中的凭证登录）：
```sql
CREATE TABLE IF NOT EXISTS price_data (
  id INT AUTO_INCREMENT PRIMARY KEY,
  trade_date DATE NOT NULL,
  trade_time TIME NOT NULL,
  data_type VARCHAR(50) NOT NULL,
  real_time_price DECIMAL(10, 4) DEFAULT 0,
  recycle_price DECIMAL(10, 4) DEFAULT 0,
  high_price DECIMAL(10, 4) DEFAULT 0,
  low_price DECIMAL(10, 4) DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_type_date (data_type, trade_date),
  INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```
验证连接：`mysql -h <host> -u <user> -p<password> <database>` 后运行 `SELECT COUNT(*) FROM price_data;`

## 常见开发任务速查

### 调试 Playwright 选择器失效
- 修改 `src/playwright_collector.py` 第 27 行：`headless=True` → `headless=False`（使用有头浏览器）
- 运行 `python src/app.py`，Playwright 会打开浏览器窗口
- 在浏览器开发者工具（F12）中用 DevTools 验证 CSS 选择器（如 `.quote-price-table .price-table-row`）
- 修复后改回 `headless=True`

### 查看日志与排查错误
- 应用日志输出到 `price_service.log`（在项目根目录）且同时打印到控制台
- MySQL 错误通常显示在日志中的 "连接池初始化" 或 "批量插入失败" 消息
- Flask 错误会显示在终端的 `INFO` 和 `ERROR` 级别

### 测试 API（使用 PowerShell）
```powershell
# 获取最新价格（不需参数，返回所有 data_type 的最新）
curl -Uri "http://localhost:8083/api/latest-price" -Method GET | ConvertFrom-Json

# 获取特定类型的最新价格
curl -Uri "http://localhost:8083/api/latest-price?data_type=黄%20金" -Method GET | ConvertFrom-Json

# 计算价格差异（POST，需要 JSON 体）
$body = @{
  product_price = 500
  weight = 10
  data_type = "黄 金"
} | ConvertTo-Json
curl -Uri "http://localhost:8083/api/calculate" -Method POST -Headers @{"Content-Type"="application/json"} -Body $body | ConvertFrom-Json
```

## API 合约与数据类型

### 标准响应格式
**成功响应**（状态码 200）：
```json
{
  "success": true,
  "data": { /* 业务数据 */ }
}
```
**失败响应**（状态码 4xx/5xx）：
```json
{
  "success": false,
  "error": "错误描述"
}
// 或（旧格式）
{
  "error": "错误描述"
}
```

### data_type 枚举值
- `黄 金` （黄金，前后各一个空格）
- `白 银` （白银，前后各一个空格）
注意：前端和后端选择器、数据库查询均使用这些精确值；修改时两端同步更新。

### 关键字段说明
- `recycle_price`：回收价格（元/克），AI 在 SQL 查询中**必须过滤** `recycle_price > 0`
- `real_time_price`：销售价格（元/克），可为 0 但通常有效数据非零
- `created_at`：数据库自动时间戳（TIMESTAMP），用于排序和追踪
- `Decimal` 类型在 JSON 中通过 `CustomJSONProvider` 自动转为浮点数

### 高级特性：SSE 价格告警与时间范围查询
- **`/api/price-alert/subscribe`**（GET，SSE）：订阅价格到达推送，参数 `data_type`, `target`, `op`(gte/lte), `auto_close`(true/false)。返回事件流：`event: price`（心跳），`event: alert`（触发），`event: ping`（保活）。
- **`/api/last-1-hour`**（GET）：获取最近 30 分钟数据，需参数 `data_type`。前端历史页面用于实时数据展示。
- **`/api/last-7-days`**（GET）：获取近 7 天每日最后一条记录的回收价，用于趋势图。需参数 `data_type`。

## 扩展点与扩展示例

### 添加新的采集数据类型
1. **前端**（`templates/index.html`）：在 `type-selector` 按钮组中新增按钮
   ```html
   <button id="typePlatin" data-type="铂 金">铂 金</button>
   ```
   并在 `<script>` 中添加点击监听：
   ```javascript
   document.getElementById('typePlatin').addEventListener('click', () => selectType('铂 金'));
   ```

2. **采集器**（`src/playwright_collector.py`）：修改选择器逻辑以支持新类型数据的提取（需确认目标网站的 HTML 结构）

3. **数据库**：新类型会自动通过 `data_type` 字段区分，无需额外列

### 添加新的查询 API（完整示例）
在 `src/route.py#create_app` 中注册新路由：
```python
@app.route('/api/custom-query', methods=['POST'])
def custom_query():
    """自定义查询示例"""
    try:
        data = request.get_json()
        data_type = data.get('data_type')
        days = data.get('days', 7)  # 默认 7 天
        
        if not data_type:
            return jsonify({'success': False, 'error': '缺少 data_type 参数'}), 400
        
        # 调用 MySQLManager 的查询方法（需在 mysql_manager.py 中新增）
        results = mysql_manager.get_data_last_n_days(data_type, days)
        
        return jsonify({'success': True, 'data': results})
    except Exception as e:
        logging.error(f"自定义查询错误: {e}")
        return jsonify({'success': False, 'error': '服务器内部错误'}), 500
```

然后在 `src/mysql_manager.py` 中新增数据库查询方法：
```python
def get_data_last_n_days(self, data_type: str, days: int) -> List[Dict]:
    query = f"""
        SELECT * FROM price_data 
        WHERE data_type = %s 
          AND recycle_price > 0 
          AND created_at >= DATE_SUB(NOW(), INTERVAL {days} DAY)
        ORDER BY created_at ASC
    """
    # 使用连接池获取、执行、关闭（参考现有 get_price_history 的模式）
```

## 不要做的事（对 AI 的明确限制）
- **数据库**：不要假设 `price_data` 之外的表；不要新增列除非明确提供迁移 SQL。仅使用 `mysql_manager.py` 中已定义的列名（`id, trade_date, trade_time, data_type, real_time_price, recycle_price, high_price, low_price, created_at`）。
- **数据过滤**：不要移除 `recycle_price > 0` 的过滤条件，除非确认业务允许零值和占位符数据。
- **响应格式**：新增 API 时必须遵循 `{success: bool, data/error: ...}` 结构，避免破坏前端解析逻辑。
- **data_type 拼写**：`黄 金` 和 `白 银` 的前后空格是精确值，不要改为其他格式（如 `黄金` 或 `黄  金`）。
- **连接池**：不要在高频路径（如 API 处理函数）中创建新的 `MySQLConnectionPool`；总是复用 `mysql_manager.connection_pool`。
- **SQL 时间函数**：使用 `created_at` 列进行时间范围查询时，注意 MySQL 函数如 `DATE_SUB(NOW(), INTERVAL 30 MINUTE)` 与北京时区的一致性。建议在 Python 中计算时间范围（使用 `datetime.now(BEIJING_TZ)`）后传入 SQL。

## 故障排查速查表

| 症状 | 原因 | 解决方案 |
|------|------|--------|
| 无法连接 MySQL | `config.ini` 中的主机/端口/凭证错误 | 运行 `mysql -h <host> -u <user> -p<password>` 验证凭证 |
| Playwright 超时 | 选择器不匹配或网页加载慢 | 改为 `headless=False` 并检查页面结构 |
| API 返回 404 | 前端调用了不存在的路由 | 在 `route.py` 中查找 `@app.route()` 装饰器确保路由已注册 |
| JSON 序列化错误 | 返回了 `Decimal` 或 `datetime` 对象 | 确保使用 `CustomJSONProvider`（在 `route.py` 中 `app.json = CustomJSONProvider(app)` 已配置） |
| 前端显示 "获取失败" | API 返回错误响应 | 查看浏览器开发者工具的 Network 标签，检查响应的 `error` 字段 |

---
**最后一步**：初次部署前，运行 `python src/app.py`，浏览器访问 `http://localhost:8083`，验证价格显示和计算功能正常。
