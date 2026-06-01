# AU 贵金属价格平台（Gold/Silver）

> 多源价格采集 → MySQL 入库 → 实时/历史/分析 → SSE 目标价提醒 → 企业微信/Telegram/邮件通知（可选）

## 目录

- [产品与能力](#产品与能力)
- [技术栈与架构](#技术栈与架构)
- [快速开始](#快速开始)
  - [方式A：仅应用容器 + 外部MySQL](#方式a仅应用容器--外部mysql)
  - [方式B：应用 + Compose内置MySQL](#方式b应用--compose内置mysql)
  - [方式C：本地Python运行（开发）](#方式c本地python运行开发)
- [环境变量](#环境变量)
- [API 与新增接口](#api-与新增接口)
- [开发与测试](#开发与测试)
- [文档](#文档)

## 产品与能力

- 实时价格概览：黄金/白银当前价、涨跌、今日高低、更新时间
- 历史与趋势：近1小时分钟线、近7天日趋势、区间趋势（OHLC）
- 分析：金银比走势
- 工具：购买价 vs 大盘价差计算、历史对比计算
- 提醒：SSE 目标价订阅（浏览器内），触发后可选多通道推送
- 数据可信度与质量：概览返回 `data_status`/`freshness_seconds`；提供质量指标接口
- 数据导出：按品类与日期范围导出 CSV/JSON（带限流与数量上限）
- 管理端（可选认证）：数据源启用/优先级/回滚、审计查询、Token 登录（见 `AUTH_ENABLED`）

## 技术栈与架构

- 后端：Python + Flask
- 数据库：MySQL（见 `scripts/init.sql`）
- 采集：多采集器并行（线程）
- 缓存：进程内 TTL 缓存（热点接口）
- 前端：Jinja2 模板页（主链路可运行）；仓库内也包含 React SPA 代码（并存）

高层链路：Collectors → MySQL → Flask API/Pages → Browser（SSE）→ Notifiers

## 快速开始

### 方式A：仅应用容器 + 外部MySQL

适合：MySQL 已在宿主机/局域网/RDS 等处部署。

1) 准备环境文件

```bash
cp .env.example .env
```

编辑 `.env`：

- 如果 MySQL 在宿主机：`MYSQL_HOST=host.docker.internal`（不要填 `127.0.0.1`）
- 如果 MySQL 在其他主机/RDS：填写可解析的主机名或 IP

2) 确保 MySQL 已执行初始化脚本

```bash
mysql -u root -p < scripts/init.sql
# 启用管理端/审计时额外执行：
mysql -u root -p price_data < scripts/migrations/002_admin_auth_audit.sql
```

3) 启动

```bash
docker compose up --build -d
```

4) 健康检查

```bash
curl -s http://localhost:8083/api/health
```

### 方式B：应用 + Compose内置MySQL

适合：本地开发联调（生产建议外部MySQL）。

```bash
cp .env.mysql.example .env.mysql
docker compose --env-file .env.mysql -f docker-compose.mysql.yml up --build -d
```

### 方式C：本地Python运行（开发）

1) 创建虚拟环境并安装依赖

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

2) 启动（需本地 MySQL 已初始化）

```bash
python src/app.py
```

默认监听：`0.0.0.0:8083`（可通过环境变量调整）。

## 环境变量

见：`.env.example`（外部MySQL）与 `.env.mysql.example`（Compose内置MySQL）。

常用：

- MySQL：`MYSQL_HOST` `MYSQL_USER` `MYSQL_PASSWORD` `MYSQL_DATABASE`
- 服务：`API_HOST` `API_PORT`
- 采集：`ENABLE_PLAYWRIGHT` `GOLD_API_INTERVAL` `WEBSITE_URL`
- 通知（可选）：`WECHAT_WEBHOOK_URL` `TELEGRAM_BOT_TOKEN` `TELEGRAM_CHAT_ID` `SMTP_*` `ALERT_EMAIL_TO`
- 认证（可选）：`AUTH_ENABLED` `AUTH_ADMIN_TOKEN` `AUTH_OPS_TOKEN` `AUTH_USER_TOKEN`；前端 `VITE_AUTH_ENABLED`（与后端一致）

## API 与新增接口

核心 API（部分）：

- `GET /api/health`
- `GET /api/price-overview`
- `GET /api/latest-price`
- `GET /api/last-1-hour?data_type=...`
- `GET /api/last-7-days?data_type=...`
- `GET /api/price-trend?data_type=...&range=7d|30d|1y|all`
- `GET /api/gold-silver-ratio?range=30d|1y|all`
- `POST /api/calculate`
- `GET /api/price-alert/subscribe?data_type=...&target=...&op=gte|lte`

新增（SRS落地）：

- `GET /api/metrics/quality`
  - 返回按 `data_type/source` 分组的 `freshness_seconds`、`missing_rate`、`collector_success_rate`（近似）等
- `GET /api/export/history?data_type=...&start_date=YYYY-MM-DD&end_date=YYYY-MM-DD&format=csv|json&limit=...`
  - 默认 `limit=5000`，上限 `20000`，并对导出做简单限流；`AUTH_ENABLED=true` 时需 admin/ops Token

认证与管理端（`AUTH_ENABLED=true` 时）：

- `GET /api/auth/me`、`POST /api/auth/session`
- `GET|PUT /api/admin/sources`、`POST /api/admin/sources/:id/rollback`
- `GET /api/admin/audit`

完整说明见 [`docs/API.md`](docs/API.md)。

## 开发与测试

静态检查：

```bash
. .venv/bin/activate
ruff check src tests
```

运行测试：

```bash
. .venv/bin/activate
pytest -q
```

## 文档

- 部署（含 GTR）：[`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)
- HTTP API：[`docs/API.md`](docs/API.md)
- 产品分析：`docs/Product_Analysis.md`
- PRD：`docs/PRD.md`
- SRS：`docs/SRS/SRS.md`（由 `docs/SRS/requirements.yml` 生成）
- SRS 附件：`docs/SRS/attachments/`
- AI 辅助开发标准化流程 (SOP)：`docs/SOP/`
  - [全生命周期SOP](docs/SOP/01_AI_Assisted_Development_SOP.md)
  - [AI 操作手册与Prompt指令](docs/SOP/02_AI_Operation_Manual.md)
  - [代码审查(CR)检查清单](docs/SOP/03_Code_Review_Checklist.md)
- Bug 修复与审查记录：`docs/bugfix/`

