# Copilot 使用说明（项目专用）

下面是让 AI 编码助理立即上手本仓库的精华说明。请只基于代码可见内容做修改。

## 一眼看懂架构
- 服务由两部分组成：数据采集（`src/playwright_collector.py`）与 HTTP API（Flask，`src/app.py` + `src/route.py`）。
- 数据流：Playwright 抓取 -> 内存缓冲 `data_buffer` -> 周期性调用 `MySQLManager.batch_insert_data` 写入 MySQL 表 `price_data` -> Flask API 从 MySQL 读取并返回给前端（`templates/index.html`）。
- 配置：所有配置通过**环境变量**管理（参见 `.env.example`），不使用配置文件。

## 关键文件与示例
- 入口与启动：`src/app.py`（`main()` 启动采集器并 run Flask）
- 路由与 API：`src/route.py`（接口：`/api/latest-price`, `/api/recent-history`, `/api/calculate`, `/api/health`, `/api/last-1-hour`, `/api/last-7-days`, `/api/price-alert/subscribe`）
- 数据库层：`src/mysql_manager.py`（使用 `mysql.connector.pooling.MySQLConnectionPool`）
- 采集器：`src/playwright_collector.py`（无头浏览器抓取、线程后台运行）
- 自定义 JSON 编码：`src/CustomJSONEncoder.py`
- 前端：`templates/index.html`（主页）、`templates/history.html`（历史趋势）

## 运行与调试
```bash
# 本地开发
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env  # 编辑 .env 填入实际配置
python src/app.py

# Docker
docker compose up --build
```

## 环境变量（.env）
| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `MYSQL_HOST` | 否 | `localhost` | MySQL 地址 |
| `MYSQL_USER` | 否 | `root` | MySQL 用户 |
| `MYSQL_PASSWORD` | **是** | - | MySQL 密码 |
| `MYSQL_DATABASE` | 否 | `price_data` | 数据库名 |
| `API_HOST` | 否 | `0.0.0.0` | Flask 绑定地址 |
| `API_PORT` | 否 | `8083` | Flask 端口 |
| `WEBSITE_URL` | **是** | - | 采集目标网站 |

## 项目约定
- **时区**：所有时间戳使用北京时区（`Asia/Shanghai`）
- **数据过滤**：SQL 查询必须包含 `recycle_price > 0`
- **data_type 值**：`黄 金`、`白 银`（含空格，精确匹配）
- **响应格式**：`{success: bool, data/error: ...}`
- **连接池**：复用 `mysql_manager.connection_pool`，不要在高频路径创建新池

## 测试 API
```bash
curl http://localhost:8083/api/health
curl http://localhost:8083/api/latest-price
curl "http://localhost:8083/api/latest-price?data_type=黄%20金"
curl -X POST http://localhost:8083/api/calculate \
  -H "Content-Type: application/json" \
  -d '{"product_price": 500, "weight": 10, "data_type": "黄 金"}'
```
