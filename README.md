# AU: 贵金属价格数据采集与分析平台

[![License: MIT](https://img.shields.io/github/license/SongYuanKun/au_mesage)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![CI](https://github.com/SongYuanKun/au_mesage/actions/workflows/python-app.yml/badge.svg)](https://github.com/SongYuanKun/au_mesage/actions)
[![Flask](https://img.shields.io/badge/flask-3.x-green)](https://flask.palletsprojects.com/)

> **在线演示**: [http://au.songyuankun.top](http://au.songyuankun.top/)

一个用于采集、存储与查询黄金/白银价格的轻量服务。默认通过 **国际金价 API、汇率 API、第三方金属价格源** 等采集器写入 MySQL；可选启用 **Playwright** 无头浏览器采集指定网站。Flask 提供 REST API 与行情分析、历史趋势等页面，数据持久化到 MySQL。

## 📋 项目概览

本项目是一个完整的金属价格采集和服务平台，包含以下核心功能：

- **多源采集**：`CollectorManager` 统一调度 Gold API、汇率、Fawaz 等采集器；可选 `ENABLE_PLAYWRIGHT=true` 启用 Playwright 站点采集
- **数据持久化**：MySQL 存储价格与汇率历史，支持批量插入与查询优化
- **REST API**：最新价、价格概览、日内/多日趋势、金银比、汇率、价格计算与提醒推送等
- **可视化展示**：主页 ECharts、近 7 天趋势页（`/history`）、行情分析页（`/analysis`）
- **容器化部署**：Dockerfile 与 docker-compose，一键启动服务

### 核心特性

✅ 多采集器并行（可配置启用 Playwright）  
✅ API 响应短期缓存（如价格概览、趋势类接口，减轻数据库压力）  
✅ 支持多种数据类型（黄金、白银，易于扩展）  
✅ JSON 序列化优化（Decimal、datetime 自动转换）  
✅ SSE 价格到达提醒 + 企业微信 / Telegram / 邮件推送（可选）  
✅ Docker 容器化（Playwright 镜像含浏览器依赖）  

---

## 🏗️ 架构设计

```
┌──────────────────────────────────────────────────────────┐
│  Collectors（后台线程，由 CollectorManager 启动）          │
│  · GoldAPICollector · ExchangeRateCollector              │
│  · Fawazahmed0Collector · [可选] PlaywrightCollector      │
└────────────────────────────┬─────────────────────────────┘
                             │ 写入 / 更新
                             ▼
┌──────────────────────────────────────────────────────────┐
│  MySQL（price_data、汇率等表）                             │
└────────────────────────────┬─────────────────────────────┘
                             │ 查询
                             ▼
┌──────────────────────────────────────────────────────────┐
│  Flask（route.py）                                        │
│  · 页面：/  /history  /analysis                          │
│  · API：latest-price、price-overview、price-trend、       │
│    gold-silver-ratio、exchange-rate、calculate、          │
│    price-alert/* …                                        │
└────────────────────────────┬─────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────┐
│  浏览器：templates + static + ECharts                    │
└──────────────────────────────────────────────────────────┘
```

---

## 📁 项目结构

```
au_mesage/
├── .env.example                  # 环境变量配置模板
├── requirements.txt              # Python 依赖列表
├── Dockerfile                    # Docker 镜像构建文件
├── docker-compose.yml            # 仅应用 + 外部 MySQL
├── docker-compose.mysql.yml      # 应用 + 内置 MySQL（本地联调）
├── .env.mysql.example            # 与 docker-compose.mysql.yml 配套
├── README.md                     # 本文件
├── CHANGELOG.md                  # 变更记录
│
├── src/
│   ├── app.py                    # 入口：MySQL、CollectorManager、Flask
│   ├── route.py                  # 应用工厂：注册 Blueprint
│   ├── application/              # 用例层：与 HTTP 无关的响应组装、区间解析（可单测）
│   │   ├── price_responses.py
│   │   ├── trend_range.py
│   │   ├── calculations.py       # /api/history、/api/calculate 的价差计算
│   │   ├── exchange.py         # /api/exchange-rate：缓存优先再查库（可单测）
│   │   └── health.py           # /api/health 响应体
│   ├── routes/
│   │   ├── pages_bp.py           # 页面路由（/、/history、/analysis）
│   │   ├── api_bp.py             # 兼容导入 → routes.api
│   │   └── api/                  # REST API 与 SSE（按领域拆分）
│   │       ├── price_routes.py
│   │       ├── alert_routes.py
│   │       └── misc_routes.py
│   ├── mysql_manager.py          # MySQL 连接池与查询
│   ├── webhook_notifier.py       # 企业微信 / Telegram / 邮件推送
│   ├── CustomJSONEncoder.py      # 自定义 JSON 序列化
│   ├── playwright_collector.py   # 旧版入口（兼容）；采集器见 collectors/
│   └── collectors/
│       ├── manager.py            # CollectorManager：统一启动采集器
│       ├── gold_api.py           # 国际金价等 API 采集
│       ├── exchange_rate.py      # 汇率采集
│       ├── fawazahmed0.py        # 第三方金属价格源
│       └── playwright_collector.py  # 可选：站点 Playwright 采集
│
├── templates/                    # Jinja2 模板
│   ├── index.html
│   ├── history.html
│   ├── analysis.html
│   └── _nav.html
├── static/css/main.css           # 样式
│
└── scripts/
    ├── init.sql                  # 数据库初始化 SQL
    └── redeploy.sh               # 部署辅助脚本（如有）
```

---

## 🚀 快速开始

### 前置要求

- **Python 3.8+**
- **MySQL 5.7+** 或 **8.0+**（生产/默认用外部库；本地可选用 `docker-compose.mysql.yml` 内置库）
- **Docker** 和 **Docker Compose**（可选）

### 本地开发

#### 1. 克隆仓库

```bash
git clone https://github.com/SongYuanKun/au_mesage.git
cd au_mesage
```

#### 2. 创建虚拟环境

```bash
python -m venv .venv
# Linux / macOS
source .venv/bin/activate
# Windows PowerShell
# .\.venv\Scripts\Activate.ps1
```

#### 3. 安装依赖

```bash
pip install -r requirements.txt
```

#### 4. 安装 Playwright 浏览器

```bash
playwright install chromium
```

#### 5. 配置环境变量

复制 `.env.example` 并填入实际配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=price_data
API_HOST=0.0.0.0
API_PORT=8083
WEBSITE_URL=https://your_website_url.com
```

#### 6. 初始化数据库

在目标库中执行 **`scripts/init.sql`**（会创建 `price_data`、`exchange_rate`、`daily_ohlc` 三张表，与代码一致）：

```bash
mysql -h <host> -u <user> -p <database> < scripts/init.sql
```

表结构以仓库内 `scripts/init.sql` 为准；勿使用旧文档中的简化建表语句。

#### 7. 启动应用

```bash
python src/app.py
```

应用将在以下地址启动：
- **Web 界面**：http://localhost:8083
- **API 基础 URL**：http://localhost:8083/api

查看日志文件：

```bash
tail -f price_service.log
```

---

## 🐳 Docker 容器化部署

提供 **两种** Compose 文件，按需选用：

| 文件 | 数据库 | 适用场景 |
|------|--------|----------|
| `docker-compose.yml` | **外部** MySQL（RDS、宿主机、局域网等） | 生产、连接已有库 |
| `docker-compose.mysql.yml` | **Compose 内** MySQL 容器 + 应用 | 本地一键起库+应用，首次执行 `scripts/init.sql` 由镜像初始化 |

两种方式**不要同时占用**同一端口（均为 `8083` / 内置方案还会占用 `3306`）。

### 方式 A：仅应用 + 外部 MySQL（推荐生产）

1. 复制 `cp .env.example .env`，填写可访问的 `MYSQL_HOST`、`MYSQL_PASSWORD` 等（库需已执行 `scripts/init.sql` 建表）。**仅应用容器 + 已有库（方案 B）** 可对照 **`.env.docker.app-only.example`**（含宿主机 / RDS 两种 `MYSQL_HOST` 写法）。宿主机本机 MySQL 还可参考 `.env.docker.host-mysql.example`。
2. 若 MySQL 跑在**宿主机**或本机其他容器映射到宿主机端口：在 `.env` 中设 `MYSQL_HOST=host.docker.internal`（`docker-compose.yml` 已含 `extra_hosts`，便于容器访问宿主机）。

```bash
docker compose -f docker-compose.yml up --build -d
```

应用：http://localhost:8083（日志目录挂载为 `./logs`）

**说明**：`docker-compose.yml` 会将 `MYSQL_HOST` / `MYSQL_USER` / `MYSQL_PASSWORD` / `MYSQL_DATABASE` 从环境变量传入容器（与根目录 `.env` 做插值合并）。若 MySQL 跑在宿主机（例如已用 `docker-compose.mysql.yml` 只起了 `mysql`、端口映射到 `3306`），容器内不能用 `127.0.0.1` 指宿主机，需使用 `MYSQL_HOST=host.docker.internal`，且账号库名须与该实例一致，例如：

```bash
MYSQL_HOST=host.docker.internal MYSQL_USER=root MYSQL_PASSWORD=<与 .env.mysql 一致> MYSQL_DATABASE=price_data \
  docker compose -f docker-compose.yml up --build -d
```

仅使用 `.env` 且其中为 `MYSQL_HOST=127.0.0.1` 时，应用容器往往**连不上**宿主机数据库，请按上式覆盖或直接把 `.env` 中的 `MYSQL_HOST` 改为 `host.docker.internal`（并核对用户、库名）。

### 方式 B：应用 + 内置 MySQL（本地联调）

1. `cp .env.mysql.example .env.mysql`，设置强密码 `MYSQL_PASSWORD`（与库 root 一致）。
2. 启动：

```bash
./scripts/docker-local-mysql.sh -d
# 或：docker compose --env-file .env.mysql -f docker-compose.mysql.yml up --build -d
```

应用：http://localhost:8083；宿主机可用 `127.0.0.1:3306` 连库调试（**勿对公网暴露**）。

### 方式 C：手动构建镜像（无 compose）

使用 `docker build` + `docker run --env-file .env`（MySQL 须对容器可达，一般为外部库）。

#### 构建镜像

```bash
docker build -t au-price-collector .
```

#### 创建 .env 文件

```env
MYSQL_HOST=your_mysql_host
MYSQL_USER=your_mysql_user
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=your_database_name
API_HOST=0.0.0.0
API_PORT=8083
```

#### 运行容器

```bash
docker run -p 8083:8083 \
  --env-file .env \
  --name au-collector \
  au-price-collector
```

#### 停止容器

```bash
docker stop au-collector
docker rm au-collector
```

---

## 📡 API 文档

### 基础信息

- **基础 URL**：`http://localhost:8083`
- **响应格式**：JSON
- **超时设置**：30 秒

### 标准响应格式

#### 成功响应（HTTP 200）

```json
{
  "success": true,
  "data": {
    "trade_date": "2025-11-24",
    "trade_time": "10:30:00",
    "data_type": "黄 金",
    "real_time_price": 585.50,
    "recycle_price": 575.30
  }
}
```

#### 失败响应（HTTP 4xx/5xx）

```json
{
  "success": false,
  "error": "错误描述信息"
}
```

### API 端点一览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 主页 |
| GET | `/history` | 近 7 天回收价趋势页 |
| GET | `/analysis` | 行情分析页 |
| GET | `/api/price-overview` | 金/银概览（涨跌、今日高低等，约 10s 缓存） |
| GET | `/api/latest-price` | 最新价格 |
| GET | `/api/recent-history` | 近期历史（图表用，最多 30 条） |
| GET | `/api/daily-history` | 指定日期的日内历史 |
| GET | `/api/last-1-hour` | 近 30 分钟内数据（需 `data_type`） |
| GET | `/api/last-7-days` | 近 7 天每日回收价 |
| GET | `/api/price-trend` | 价格趋势：`range`=1d/7d/30d/90d/1y/all |
| GET | `/api/gold-silver-ratio` | 金银比走势 |
| GET | `/api/exchange-rate` | 最新汇率（默认 USD/CNY） |
| GET | `/api/alert-channels` | 已配置的提醒推送渠道 |
| POST | `/api/price-alert/push` | 按阈值检查并可选多通道推送 |
| GET | `/api/price-alert/subscribe` | SSE 价格心跳与到达提醒 |
| POST | `/api/history` | 根据总价与重量计算每克价并与大盘对比 |
| POST | `/api/calculate` | 购买场景价格与大盘差异计算 |
| GET | `/api/health` | 健康检查 |

---

#### 1. 获取最新价格

**端点**：`GET /api/latest-price`

**参数**（可选）：
- `data_type` (string)：数据类型，如 `黄 金`、`白 银`（若不指定则返回所有类型的最新价格）

**请求示例**：

```bash
# 获取所有类型的最新价格
curl http://localhost:8083/api/latest-price

# 获取特定类型（黄金）的最新价格
curl "http://localhost:8083/api/latest-price?data_type=黄%20金"
```

**响应示例**：

```json
{
  "success": true,
  "data": [
    {
      "trade_date": "2025-11-24",
      "trade_time": "14:30:00",
      "data_type": "黄 金",
      "real_time_price": 585.50,
      "recycle_price": 575.30
    },
    {
      "trade_date": "2025-11-24",
      "trade_time": "14:30:00",
      "data_type": "白 银",
      "real_time_price": 8.20,
      "recycle_price": 7.95
    }
  ]
}
```

---

#### 2. 获取历史价格数据（图表用）

**端点**：`GET /api/recent-history`

**参数**（必需）：
- `data_type` (string)：数据类型，如 `黄 金`、`白 银`

**查询限制**：最多返回最近 30 条数据点（用于前端图表展示）

**请求示例**：

```bash
curl "http://localhost:8083/api/recent-history?data_type=黄%20金"
```

**响应示例**：

```json
{
  "success": true,
  "data": [
    {
      "trade_date": "2025-11-24",
      "trade_time": "10:00:00",
      "data_type": "黄 金",
      "real_time_price": 580.00,
      "recycle_price": 570.00
    },
    {
      "trade_date": "2025-11-24",
      "trade_time": "10:30:00",
      "data_type": "黄 金",
      "real_time_price": 582.50,
      "recycle_price": 572.50
    },
    ...
  ]
}
```

---

#### 3. 价格计算接口（购买 vs 大盘）

**端点**：`POST /api/calculate`

**请求体**（JSON）：`product_price`（商品总价）、`weight`（克重）、`data_type`；可选 `calculation_type`（默认 `purchase`）。

**响应字段**（节选）：`price_per_gram`、`market_price`（回收价作大盘参考）、`difference`、`difference_percentage`、`total_difference`、`message_prefix` 等。

详见 `src/route.py` 中 `calculate_price_difference`。

---

#### 4. 健康检查

**端点**：`GET /api/health`

**请求示例**：`curl http://localhost:8083/api/health`

**响应示例**：

```json
{
  "status": "healthy",
  "timestamp": "2025-11-24T14:30:00+08:00",
  "service": "price-data-api"
}
```

---

#### 5. 价格到达提醒（SSE）

**端点**：`GET /api/price-alert/subscribe`

**查询参数**：
- `data_type`：如 `黄 金`、`白 银`
- `target`：目标价（元/克）
- `op`：`gte`（≥）或 `lte`（≤），默认 `gte`
- `auto_close`：命中后是否关闭连接，默认 `true`

**响应**：`text/event-stream`（`event: price` / `alert` / `ping`）。命中阈值时可触发 `webhook_notifier` 已配置的渠道。

**前端示例**：

```javascript
const url = `/api/price-alert/subscribe?data_type=黄%20金&target=585.0&op=gte&auto_close=true`;
const es = new EventSource(url);
es.addEventListener('price', ev => console.log('price', JSON.parse(ev.data)));
es.addEventListener('alert', ev => console.log('alert', JSON.parse(ev.data)));
```

---

#### 6. 其他接口说明

- **`GET /api/price-overview`**：返回各 `data_type` 的当前价、相对昨收涨跌、今日高低等（服务端短期缓存）。
- **`GET /api/price-trend`**：参数 `data_type`、`range`（`1d` 为分钟线，其余为日 K OHLC）。
- **`GET /api/exchange-rate`**：参数 `base`、`target`（默认 USD/CNY），优先内存缓存。
- **`POST /api/price-alert/push`**：JSON 传入 `data_type`、`target`、`op`、`channels`（`wechat` / `telegram` / `email`），用于主动检查并推送。

更完整的参数与字段以源码为准：`src/route.py`。

---

## 🔧 配置说明

### 环境变量说明

所有配置通过环境变量管理，参见 `.env.example`：

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `MYSQL_HOST` | 否 | `localhost` | MySQL 服务器地址 |
| `MYSQL_USER` | 否 | `root` | MySQL 用户名 |
| `MYSQL_PASSWORD` | **是** | - | MySQL 密码 |
| `MYSQL_DATABASE` | 否 | `price_data` | 数据库名 |
| `API_HOST` | 否 | `0.0.0.0` | Flask 绑定地址 |
| `API_PORT` | 否 | `8083` | Flask 监听端口 |
| `WEBSITE_URL` | 条件必填 | - | Playwright 启用时：采集目标网站 |
| `ENABLE_PLAYWRIGHT` | 否 | `false` | `true` 时启用 Playwright 站点采集 |
| `GOLD_API_INTERVAL` | 否 | `60` | 国际金价 API 采集间隔（秒） |
| `WECHAT_WEBHOOK_URL` 等 | 否 | - | 价格提醒推送，见 `.env.example` |

---

## 📊 数据库模式

以下与 **`scripts/init.sql`** 保持一致；应用写入逻辑见 `src/mysql_manager.py`。

### `price_data`（实时/站点与 API 价格流水）

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `id` | INT，自增主键 | 主键 |
| `trade_date` / `trade_time` | DATE / TIME | 交易日期与时间 |
| `data_type` | VARCHAR(50) | 数据类型（如黄金、白银） |
| `real_time_price` / `recycle_price` | DECIMAL(10,4) | 实时价、回收价 |
| `high_price` / `low_price` | DECIMAL(10,4) | 高低价 |
| `source` | VARCHAR(30) | 数据来源（如 `gold_api`、`exchange_rate`、`fawazahmed0`、`playwright`） |
| `currency` | VARCHAR(10) | 计价币种（如 CNY、USD） |
| `created_at` | TIMESTAMP | 写入时间 |

主要索引：`idx_type_created`、`idx_date_type_recycle`、`idx_type_date_created`、`idx_source`（见 `init.sql`）。

### `exchange_rate`（汇率记录）

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `base_currency` / `target_currency` | VARCHAR(10) | 货币对 |
| `rate` | DECIMAL(12,6) | 汇率 |
| `source` | VARCHAR(30) | 来源标识 |
| `created_at` | TIMESTAMP | 写入时间 |

### `daily_ohlc`（日线 OHLC，如 Fawaz 等源）

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `trade_date` | DATE | 交易日 |
| `data_type` / `source` | VARCHAR | 品种与来源 |
| `currency` | VARCHAR(10) | 币种 |
| `open_price` … `close_price` | DECIMAL(12,4) | OHLC |
| `volume` | DECIMAL(20,4)，可空 | 成交量 |
| `created_at` | TIMESTAMP | 更新时间 |

唯一约束：`uk_date_type_source`（`trade_date`, `data_type`, `source`），供 `INSERT … ON DUPLICATE KEY UPDATE` 使用。

---

## 🔍 核心模块说明

### 1. app.py（应用入口）

**职责**：
- 初始化日志、加载配置、创建 `MySQLManager`
- 通过 `CollectorManager` 启动全部采集器（见 `src/collectors/manager.py`）
- `create_app(mysql_manager)` 注册 Flask 路由；退出时 `stop_all()` 停止采集器

**日志文件**：由 `setup_logging()` 中的 `FileHandler` 路径决定，与**运行时的当前工作目录**有关；若需固定到仓库根目录，可改为基于 `__file__` 的绝对路径。

```bash
python src/app.py
```

---

### 2. route.py 与 routes/（页面与 REST API）

**职责**：`route.create_app` 使用绝对路径挂载 `templates/`、`static/`，并注册 `routes/pages_bp.py`（`/`、`/history`、`/analysis`）与 `routes.api.create_api_blueprint`（`/api/*` 与 SSE，拆分为 `routes/api/{price,alert,misc}_routes.py`）；价格类 JSON 组装在 `application/price_responses.py`；趋势区间解析在 `application/trend_range.py`；进程内 TTL 缓存在 `routes/api/cache.py`（`TtlCache`）。

**特性**：`CustomJSONProvider`；北京时间 `Asia/Shanghai` 用于日期与展示。

---

### 2.1 collectors/manager.py（采集调度）

**职责**：实例化 `GoldAPICollector`、`ExchangeRateCollector`、`Fawazahmed0Collector`；当 `ENABLE_PLAYWRIGHT=true` 时再挂载 `collectors/playwright_collector.py` 中的 `PlaywrightCollector`。

---

### 3. mysql_manager.py（数据库管理）

**职责**：
- 管理 MySQL 连接池
- 执行数据库查询和插入操作
- 提供数据库接口给其他模块

**关键类**：`MySQLManager`

**关键方法**：
- `get_latest_data(data_type)`：获取特定类型的最新价格
- `get_latest_data_by_type()`：获取所有类型的最新价格
- `get_price_history(data_type, limit=30)`：获取历史价格数据
- `batch_insert_data(data_list)`：批量写入 `price_data`
- `upsert_exchange_rate` / `get_latest_exchange_rate`：汇率表
- `upsert_daily_ohlc` / `get_daily_ohlc`：日线表
- `get_connection()`：从连接池获取连接

**连接池配置**：
- 池名：`price_pool`
- 默认大小：5 个连接
- 支持自动重连

**查询优化**：
- 使用参数化查询防止 SQL 注入
- 批量插入提高性能
- 索引优化查询速度

---

### 4. Playwright 采集器（可选）

**位置**：`src/collectors/playwright_collector.py`（由 `CollectorManager` 在 `ENABLE_PLAYWRIGHT=true` 时加载）

**职责**：无头 Chromium 访问 `WEBSITE_URL`，解析页面写入 MySQL；具体间隔与缓冲逻辑见该文件。

**调试**：将浏览器改为有头模式、调整选择器时，请在该采集器源码中修改（勿与根目录遗留的 `src/playwright_collector.py` 混淆，后者用于兼容旧引用）。

---

### 5. CustomJSONEncoder.py（JSON 序列化）

**职责**：
- 自定义 Flask JSON 编码器
- 将不支持的类型（Decimal、datetime）转换为 JSON 兼容的类型

**支持的转换**：
- `datetime` → ISO 8601 字符串
- `date` → ISO 格式字符串
- `Decimal` → float
- `timedelta` → 秒数

**使用**：

```python
# 在 route.py 中配置
from CustomJSONEncoder import CustomJSONProvider
app.json = CustomJSONProvider(app)
```

---

## 🐛 调试指南

### 1. 检查数据库连接

```bash
# 使用 MySQL 命令行
mysql -h your_mysql_host -u your_mysql_user -p
# 输入密码后
SELECT COUNT(*) FROM price_data;
```

### 2. 调试 Playwright 选择器

在 `src/collectors/playwright_collector.py` 中改为有头运行（`headless=False`），便于用开发者工具检查选择器。

### 3. 查看实时日志

```bash
tail -f price_service.log
```

### 4. 测试 API 端点

```bash
# 健康检查
curl http://localhost:8083/api/health

# 获取最新价格
curl http://localhost:8083/api/latest-price

# 获取历史数据
curl "http://localhost:8083/api/recent-history?data_type=黄%20金"
```

### 5. 常见问题排查

| 问题 | 原因 | 解决方案 |
|------|------|--------|
| 无法连接 MySQL | 配置错误或 MySQL 未运行 | 检查 `.env` 环境变量和 MySQL 服务状态 |
| Playwright 超时 | 页面加载慢或选择器不匹配 | 改为 `headless=False` 调试 |
| JSON 序列化错误 | 返回类型不兼容 | 确保使用 CustomJSONProvider |
| API 返回 404 | 路由未注册 | 检查 `route.py` 中的 `@app.route()` 定义 |
| 采集数据为 0 | 上游接口/页面变更或未启用对应采集器 | 查看采集器日志；Playwright 路径检查 `ENABLE_PLAYWRIGHT` 与选择器 |

---

## 📈 数据采集流程详解

### 采集周期（概览）

**默认（API 类采集器）**：`CollectorManager` 启动各采集器线程，按各自间隔请求 HTTP/API，解析后写入 MySQL（实现见 `src/collectors/*.py`）。

**可选（Playwright）**：当 `ENABLE_PLAYWRIGHT=true` 时，额外启动浏览器采集：访问 `WEBSITE_URL`、解析 DOM，通常配合内存缓冲与周期性 `batch_insert_data()` 落库，具体间隔与缓冲以 `src/collectors/playwright_collector.py` 为准。

### 性能优化点

✅ **多采集器并行**：金属价、汇率等分源采集  
✅ **批量插入**：减少数据库往返（各采集器内部策略不同）  
✅ **后台线程**：采集不阻塞 Flask API  
✅ **连接池**：复用 MySQL 连接  
✅ **只读接口缓存**：部分路由对热点查询做短时 TTL 缓存  
✅ **索引**：见 `scripts/init.sql` 与表设计  

---

## 🚢 生产部署

### Docker 部署步骤

#### 1. 构建镜像

```bash
docker build -t au-price-collector:1.0 .
```

#### 2. 创建 .env 文件（存放敏感信息）

```env
MYSQL_HOST=your-production-mysql-host
MYSQL_USER=production-user
MYSQL_PASSWORD=strong-password-here
MYSQL_DATABASE=production-db
API_HOST=0.0.0.0
API_PORT=8083
```

#### 3. 使用 docker-compose 启动

```bash
docker-compose up -d
```

#### 4. 查看日志

```bash
docker-compose logs -f app
```

#### 5. 停止服务

```bash
docker-compose down
```

### 网络配置

#### 端口映射

```yaml
# docker-compose.yml
ports:
  - "8083:8083"  # 本机 8083 端口映射到容器 8083 端口
```

#### 环境网络访问

如需外部访问，确保 `.env` 中设置：

```env
API_HOST=0.0.0.0
API_PORT=8083
```

#### 防火墙配置

```bash
# Linux (ufw)
ufw allow 8083/tcp

# macOS 默认不需要配置
```

### 监控和维护

#### 检查容器状态

```bash
docker ps -a  # 查看所有容器

docker stats   # 实时监控容器资源使用
```

#### 查看容器日志

```bash
docker logs -f my-au              # 查看最新日志
docker logs my-au --tail 100      # 查看最后 100 行
```

#### 进入容器调试

```bash
docker exec -it my-au /bin/bash
```

---

## 🔐 安全建议

1. **数据库密码**：使用环境变量而非配置文件硬编码
2. **API 认证**：在生产环境添加 API Token 验证（可扩展）
3. **HTTPS**：在生产环境使用 HTTPS（配置反向代理如 Nginx）
4. **日志管理**：定期清理日志文件防止磁盘爆满
5. **数据备份**：定期备份 MySQL 数据库

---

## 📚 扩展与自定义

### 添加新的数据类型

#### 步骤 1：修改前端（templates/index.html）

```html
<!-- 在数据类型选择器中添加新按钮 -->
<button id="typePlatin" data-type="铂 金">铂 金</button>
```

```javascript
// 在 JavaScript 中添加点击监听
document.getElementById('typePlatin').addEventListener('click', () => selectType('铂 金'));
```

#### 步骤 2：修改采集器

在 `src/collectors/playwright_collector.py`（若启用）或相应 API 采集器中更新解析逻辑以支持新数据类型。

#### 步骤 3：数据库

新类型会自动通过 `data_type` 字段区分，无需修改表结构。

### 添加新的 API 端点

在 `src/route.py` 中注册新路由：

```python
@app.route('/api/custom-query', methods=['POST'])
def custom_query():
    """自定义查询示例"""
    try:
        data = request.get_json()
        data_type = data.get('data_type')
        days = data.get('days', 7)
        
        if not data_type:
            return jsonify({'success': False, 'error': '缺少 data_type 参数'}), 400
        
        results = mysql_manager.get_data_last_n_days(data_type, days)
        return jsonify({'success': True, 'data': results})
    except Exception as e:
        logging.error(f"自定义查询错误: {e}")
        return jsonify({'success': False, 'error': '服务器内部错误'}), 500
```

---

## 📝 日志管理

### 日志文件位置

日志文件路径由 `src/app.py` 中 `FileHandler` 指定，实际位置取决于**启动进程时的当前工作目录**。

### 日志级别

```
INFO     - 一般信息（启动、采集数据等）
ERROR    - 错误信息（数据库连接失败、采集异常等）
WARNING  - 警告信息（超时、重试等）
```

### 日志格式

```
2025-11-24 10:30:00,123 - root - INFO - 应用启动成功
2025-11-24 10:31:00,456 - root - INFO - 批量插入 5 条数据到数据库
2025-11-24 10:35:00,789 - root - ERROR - 数据库连接失败: Connection refused
```

### 日志查看

```bash
# 实时查看（持续跟踪）
tail -f price_service.log

# 搜索错误日志
grep "ERROR" price_service.log

# 按日期过滤
grep "2025-11-24" price_service.log
```

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

### 本地开发流程

1. Fork 仓库
2. 创建特性分支：`git checkout -b feature/your-feature`
3. 提交更改：`git commit -am 'Add your feature'`
4. 推送到分支：`git push origin feature/your-feature`
5. 提交 Pull Request

### 单元测试

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
PYTHONPATH=src pytest tests/ -v
```

当前覆盖进程内 TTL 缓存等可纯逻辑验证的模块；涉及 Flask/MySQL 的接口可后续用测试客户端与夹具扩展。

### 代码规范

- 遵循 PEP 8 Python 代码规范
- 添加适当的注释和文档字符串
- 确保所有单元测试通过
- 更新 README 文档

---

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

---

## 👤 作者

***SongYuanKun***

- GitHub：[@SongYuanKun](https://github.com/SongYuanKun)
- 项目地址：[au_mesage](https://github.com/SongYuanKun/au_mesage)

---

## 📞 支持与反馈

如有问题或建议，请：

1. 提交 GitHub Issues
2. 发送邮件反馈
3. 查看 FAQ 部分

---

## 🎯 项目路线图

- [ ] 支持更多数据类型（铂金、钯金等）
- [ ] 添加用户认证系统
- [ ] 实现数据导出功能（Excel、CSV）
- [x] 服务端推送：SSE `/api/price-alert/subscribe` + 可选 Webhook / 邮件
- [ ] 性能监控面板
- [ ] 多语言支持（English、日本語）
- [ ] 移动端应用
- [ ] 数据分析和预测功能

---

## ❓ FAQ

### Q: 采集数据多久更新一次？
A: 国际金价等 API 采集间隔由 `GOLD_API_INTERVAL`（秒）控制。启用 Playwright 时，间隔与落库策略见 `src/collectors/playwright_collector.py`。

### Q: 如何修改采集网站？
A: 设置 `ENABLE_PLAYWRIGHT=true` 并配置 `WEBSITE_URL`，在 `src/collectors/playwright_collector.py` 中调整 URL 与选择器。

### Q: 数据库备份策略？
A: 建议使用 MySQL 自带的 `mysqldump` 工具或配置主从复制。

### Q: 如何在生产环境中运行？
A: 使用 Docker Compose 或 Kubernetes，配合 Nginx 反向代理和 SSL/TLS 证书。

### Q: 支持数据导出吗？
A: 当前不支持，但可以通过 SQL 查询直接导出。可在路线图中考虑实现此功能。

---

## 📊 性能指标

基于当前配置的参考性能指标（随启用采集器与负载变化）：

- **API 响应时间**：简单查询多在百毫秒级以内（部分接口带缓存）
- **采集间隔**：API 类由 `GOLD_API_INTERVAL` 等控制；Playwright 启用时另有页面轮询与缓冲写入
- **内存占用**：仅 API 采集时显著低于运行 Chromium 的场景；启用 Playwright 时约数百 MB 级
- **CPU 占用**：视采集频率与浏览器是否启用而定

---

**Last Updated**: 2026年3月20日  
**Version**: 1.1.1  
**Status**: ✅ Production Ready
