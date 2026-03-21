# Copilot 使用说明（项目专用）

下面是让 AI 编码助理立即上手本仓库的精华说明。请只基于代码可见内容做修改。

## 一眼看懂架构
- **采集**：`src/collectors/manager.py` 中的 `CollectorManager` 统一启动多个采集器线程（`gold_api`、`exchange_rate`、`fawazahmed0` 等）；`ENABLE_PLAYWRIGHT=true` 时再挂载 `src/collectors/playwright_collector.py`。
- **数据流**：各采集器写入 MySQL（如 `price_data`、汇率相关表）→ Flask（`src/route.py`）查询并返回 JSON / 渲染 `templates/`。
- **数据库**：生产用**外部 MySQL** + `docker-compose.yml`（仅应用）。本地联调可用 `docker-compose.mysql.yml` + `.env.mysql` 起内置 MySQL。
- **配置**：环境变量（见 `.env.example`），无独立配置文件。

## 关键文件
- 入口：`src/app.py`（`MySQLManager`、`CollectorManager.start_all()`、`create_app().run()`）
- 路由：`src/route.py`（页面 `/`、`/history`、`/analysis`；API 含 `price-overview`、`price-trend`、`gold-silver-ratio`、`exchange-rate`、`price-alert/*` 等）
- 数据库：`src/mysql_manager.py`
- 推送：`src/webhook_notifier.py`（企业微信 / Telegram / 邮件，可选）
- JSON：`src/CustomJSONEncoder.py`
- 前端：`templates/`、`static/css/main.css`

## 运行与调试
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# 仅当 ENABLE_PLAYWRIGHT=true 时需要：
# playwright install chromium
python src/app.py
```

## 环境变量（节选）
| 变量 | 说明 |
|------|------|
| `MYSQL_*` / `API_*` | 数据库与 Flask 监听 |
| `ENABLE_PLAYWRIGHT` | 默认 `false`；`true` 时启用站点 Playwright 采集 |
| `WEBSITE_URL` | Playwright 启用时：目标站点 |
| `GOLD_API_INTERVAL` | 国际金价 API 采集间隔（秒） |
| `WECHAT_WEBHOOK_URL` 等 | 价格提醒推送（可选） |

## 项目约定
- **时区**：业务日期时间多用北京时区 `Asia/Shanghai`（见 `route.py`）
- **data_type**：如 `黄 金`、`白 银`（含空格，与库内一致）
- **API 风格**：多数接口为 `{ "success": true/false, "data": ... }`；部分计算器接口返回字段与 `success` 混用，改前对照 `route.py`

## 测试 API
```bash
curl http://localhost:8083/api/health
curl http://localhost:8083/api/price-overview
curl "http://localhost:8083/api/latest-price?data_type=黄%20金"
```
