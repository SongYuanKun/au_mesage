# 代码审查与Bug修复说明（2026-05-13）

## 范围

本次审查覆盖以下变更相关文件：

- 后端错误处理与路由：`src/route.py`、`src/api_errors.py`、`src/routes/api/*.py`
- 概览/指标/导出：`src/application/price_responses.py`、`src/application/metrics.py`、`src/db/price_reader.py`
- 通知日志脱敏：`src/webhook_notifier.py`
- 测试：`tests/*`

## 发现的问题与修复

### 1) 全局 404/405 JSON 错误响应影响非 API 页面

- **问题表现**：访问不存在的页面路径（例如 `/nope`）会返回 JSON 错误结构，影响页面侧的用户体验与错误页表现。
- **根因**：`@app.errorhandler(404/405)` 是全局生效，未区分 `/api/*` 与页面路由。
- **修复方案**：对 `request.path` 做前缀判断，仅对 `/api/` 返回统一 JSON 错误；非 API 返回简单文本响应。
- **影响面**：仅改变 404/405 的响应内容；不影响已有 API 错误结构。

相关改动：`src/route.py`

### 2) 导出接口限流窗口“滑动”导致语义偏差

- **问题表现**：限流计数每次请求都会刷新 TTL，导致窗口行为更接近滑动窗口，且在高频请求下可能导致长时间无法自然重置。
- **根因**：限流实现复用了 `TtlCache` 的写入时间戳作为过期判定，且每次更新都会写入刷新时间。
- **修复方案**：在桶内保存 `start` 时间，并显式判断 `now-start > window_seconds` 后重置；TTL 仅作为内存自动清理手段。
- **验证**：新增单测覆盖“超过阈值阻断”和“窗口后重置”。

相关改动：`src/routes/api/rate_limit.py`、`tests/test_rate_limit.py`

### 3) 导出接口的边界条件与兼容性问题

- **问题表现**：
  - `X-Forwarded-For` 可能包含多个IP，直接使用会导致限流key不可控。
  - 导出量无限制时，可能一次性加载大量数据到内存（CSV/JSON均为内存构建），存在OOM风险。
  - `Content-Disposition` 对中文文件名兼容性不稳定。
- **根因**：缺少对代理头解析、导出上限与下载头标准化处理。
- **修复方案**：
  - 只取 `X-Forwarded-For` 的首个IP作为限流依据。
  - 增加 `limit` 参数并设置最大值（默认5000，上限20000），减少一次导出的内存风险。
  - 采用 `filename*`（RFC 5987）形式提供UTF-8文件名，同时保留ASCII回退。

相关改动：`src/routes/api/misc_routes.py`、`src/db/price_reader.py`、`tests/test_export.py`

## 静态分析与测试

### 回归测试

- 执行：`pytest -q`
- 结果：全部通过（包含新增限流测试）。

### 静态检查（建议）

- 建议引入 `ruff`（或 `flake8`）进行持续静态检查，并在 CI 中强制失败。

## 风险与后续建议

- `/api/export/history` 当前为“进程内限流”，多实例部署时需要迁移到 Redis/网关限流以保证一致性。
- `/api/metrics/quality` 的 `collector_success_rate` 为基于写入点数的近似指标，若要严格定义成功率，需要采集尝试日志或任务表。
