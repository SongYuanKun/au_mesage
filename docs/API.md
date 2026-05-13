# HTTP API 说明

基路径：与前端同源部署时无前缀；本地开发默认由 Vite 代理到后端（见 `vite.config`）。  
统一 JSON 字段约定：

- 成功：`{ "success": true, "data": ... }`（部分旧接口仍可能仅返回业务字段，以各节为准）
- 失败（`/api/*`）：`{ "success": false, "error": { "code", "message", "details?" } }`，HTTP 状态码与 `code` 对齐（见 `src/api_errors.py`）

## 健康与指标

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 存活探测，返回时间与状态 |
| GET | `/api/metrics/quality` | 数据质量聚合（新鲜度、近一小时计数等） |

## 价格与趋势

| 方法 | 路径 | 查询参数 / 体 | 说明 |
|------|------|----------------|------|
| GET | `/api/price-overview` | — | 黄金/白银概览（短 TTL 缓存） |
| GET | `/api/latest-price` | `data_type?` | 无参则返回多品类最新一条；有参则按品类 |
| GET | `/api/recent-history` | `data_type`（必填） | 近期历史（图表用，约 30 条） |
| GET | `/api/daily-history` | `date?`（默认今日）, `data_type?` | 某日明细 |
| GET | `/api/last-1-hour` | `data_type` | 近 1 小时点位 |
| GET | `/api/last-7-days` | `data_type` | 近 7 日日线 |
| GET | `/api/price-trend` | `data_type`, `range`（默认 `7d`） | `1d` 为分钟线；其余为日 K OHLC |
| GET | `/api/gold-silver-ratio` | `range`（默认 `30d`） | 金银比时间序列 |

`range` 合法值与错误信息由 `application.trend_range` 解析逻辑决定（非法值返回 400）。

## 计算与导出

| 方法 | 路径 | 体 / 查询 | 说明 |
|------|------|-----------|------|
| POST | `/api/calculate` | JSON：`product_price`, `weight`, `data_type` | 购买价与大盘价差 |
| POST | `/api/history` | JSON：`product_price`, `weight`, `data_type` | 与历史大盘对比 |
| GET | `/api/exchange-rate` | `base?`（默认 USD）, `target?`（默认 CNY） | 汇率 |
| GET | `/api/export/history` | `data_type`, `start_date`, `end_date`, `format?`（csv/json）, `limit?` | 导出；按 IP 限流（见 `rate_limit`） |

## 提醒与推送

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/alert-channels` | 已配置渠道列表 |
| POST | `/api/price-alert/push` | JSON：`data_type`, `target`, `op`（`gte`/`lte`）, `channels[]` |
| GET | `/api/price-alert/subscribe` | SSE：`data_type`, `target`, `op`, `auto_close`；事件含 `ping`/`price`/`alert` |

## 页面路由（非 API）

| 方法 | 路径 |
|------|------|
| GET | `/` |
| GET | `/history` |
| GET | `/analysis` |

## 版本与变更

API 行为变更应同步更新本文件，并在 `CHANGELOG.md` 中记录对应版本与 SRS 需求编号（若有）。
