# AU Metal Price Platform (Gold/Silver)

> Multi-source collection → MySQL storage → Realtime/History/Analysis → SSE target-price alerts → Optional notifications (WeCom/Telegram/Email)

## Contents

- [Product & Features](#product--features)
- [Tech Stack & Architecture](#tech-stack--architecture)
- [Quick Start](#quick-start)
  - [Option A: App container + external MySQL](#option-a-app-container--external-mysql)
  - [Option B: App + MySQL via Docker Compose](#option-b-app--mysql-via-docker-compose)
  - [Option C: Run with local Python (dev)](#option-c-run-with-local-python-dev)
- [Environment Variables](#environment-variables)
- [APIs & New Endpoints](#apis--new-endpoints)
- [Development & Testing](#development--testing)
- [Docs](#docs)

## Product & Features

- Realtime overview: gold/silver current price, change, daily high/low, updated time
- History & trend: last 1 hour (minute series), last 7 days (daily series), OHLC trend by range
- Analysis: gold/silver ratio
- Tools: purchase price vs market spread, history comparison
- Alerts: SSE target-price subscription (in-browser), optional multi-channel notifications
- Data trust & quality: overview includes `data_status`/`freshness_seconds`; quality metrics endpoint available
- Export: export history as CSV/JSON with rate limit and max row limit

## Tech Stack & Architecture

- Backend: Python + Flask
- Database: MySQL (schema in `scripts/init.sql`)
- Collectors: multiple collectors running concurrently (threads)
- Cache: in-process TTL cache for hot APIs
- Frontend: Jinja2 template pages (runnable main path); React SPA code also exists in the repo

High-level flow: Collectors → MySQL → Flask API/Pages → Browser (SSE) → Notifiers

## Quick Start

### Option A: App container + external MySQL

Use this if your MySQL is already running (host machine/LAN/RDS).

1) Prepare env file

```bash
cp .env.example .env
```

Edit `.env`:

- If MySQL runs on the host machine: set `MYSQL_HOST=host.docker.internal` (do NOT use `127.0.0.1`)
- If MySQL is remote: set `MYSQL_HOST` to a resolvable hostname/IP

2) Initialize MySQL schema

```bash
mysql -u root -p < scripts/init.sql
```

3) Start

```bash
docker compose up --build -d
```

4) Health check

```bash
curl -s http://localhost:8083/api/health
```

### Option B: App + MySQL via Docker Compose

Use this for local development (production should use external MySQL).

```bash
cp .env.mysql.example .env.mysql
docker compose --env-file .env.mysql -f docker-compose.mysql.yml up --build -d
```

### Option C: Run with local Python (dev)

1) Create venv and install dependencies

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

2) Start (requires local MySQL initialized)

```bash
python src/app.py
```

Default listen: `0.0.0.0:8083` (configurable via env vars).

## Environment Variables

See `.env.example` (external MySQL) and `.env.mysql.example` (Compose MySQL).

Common:

- MySQL: `MYSQL_HOST` `MYSQL_USER` `MYSQL_PASSWORD` `MYSQL_DATABASE`
- Server: `API_HOST` `API_PORT`
- Collectors: `ENABLE_PLAYWRIGHT` `GOLD_API_INTERVAL` `WEBSITE_URL`
- Notifications (optional): `WECHAT_WEBHOOK_URL` `TELEGRAM_BOT_TOKEN` `TELEGRAM_CHAT_ID` `SMTP_*` `ALERT_EMAIL_TO`

## APIs & New Endpoints

Core APIs (partial list):

- `GET /api/health`
- `GET /api/price-overview`
- `GET /api/latest-price`
- `GET /api/last-1-hour?data_type=...`
- `GET /api/last-7-days?data_type=...`
- `GET /api/price-trend?data_type=...&range=7d|30d|1y|all`
- `GET /api/gold-silver-ratio?range=30d|1y|all`
- `POST /api/calculate`
- `GET /api/price-alert/subscribe?data_type=...&target=...&op=gte|lte`

New (SRS-backed):

- `GET /api/metrics/quality`
  - Grouped by `data_type/source`, returns `freshness_seconds`, `missing_rate`, and approximated `collector_success_rate`
- `GET /api/export/history?data_type=...&start_date=YYYY-MM-DD&end_date=YYYY-MM-DD&format=csv|json&limit=...`
  - Default `limit=5000`, max `20000`, and basic rate limiting for export

## Development & Testing

Static check:

```bash
. .venv/bin/activate
ruff check src tests
```

Unit tests:

```bash
. .venv/bin/activate
pytest -q
```

## Docs

- Product analysis: `docs/Product_Analysis.md`
- PRD: `docs/PRD.md`
- SRS: `docs/SRS/SRS.md` (generated from `docs/SRS/requirements.yml`)
- SRS attachments: `docs/SRS/attachments/`
- Bugfix & review notes: `docs/bugfix/`

