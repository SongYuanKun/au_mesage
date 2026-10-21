# AU 审查后修复记录（2026-10-21）

## 已修复

- `/api/health` 现在是 readiness：数据库查询成功、且至少一条价格未超过
  `HEALTH_MAX_DATA_AGE_SECONDS`（默认 600 秒）才返回 `200/healthy`；数据库不可用、
  无数据、陈旧数据和超容差未来数据均返回 `503/unhealthy`。
  aware 时间一律转 UTC；MySQL 返回的 naive `created_at` 按请求时间戳的时区解释。
  当前路由使用 `Asia/Shanghai`，与数据库 `CURRENT_TIMESTAMP` 的既有本地时间口径一致。
- 提醒 SSE 仅发 `price/alert/ping` 事件，不再在 GET 请求中调用外部通知。
  外部推送仅能通过 `POST /api/price-alert/push`，即使 `AUTH_ENABLED=false` 也必须是
  已配置的 Bearer 用户、运维或管理员 Token。会话 Cookie 只可用于同源 SSE/渠道读取，
  不能授权推送写操作。
- 提醒限流按不可逆 Token 主体摘要区分，不记录原 Token；匿名 SSE 回退到
  `remote_addr`。渠道读取为 30 次/分钟，推送与 SSE 建连各为 10 次/分钟。
- Playwright 在页面关闭、断连和连续失败后继续重建浏览器并指数退避；报价中的 `--`、
  `—` 等占位值作为缺失行跳过，不再写入伪 0 价格或产生每分钟 ERROR。
- 文件日志改为 10 MiB、保留 5 份的轮转日志。金银比查询只允许同一来源、币种和
  国内/国际市场口径的金银数据配对。
- React API 客户端改为匹配后端扁平的 `calculate/history` 字段和
  `{success, channels}` 提醒渠道响应；首页旧模板在国际 `USD/oz` 报价时只在获得
  USD/CNY 并切换到人民币/克后计算，否则明确拒绝计算。
- 数据源 priority 现在决定启用源的启动顺序（较小优先级先启动）。

## 验证

```text
/home/kun/vs_code/au/.venv/bin/python -m pytest -q \
  tests/test_health.py tests/test_app_factory.py tests/test_alert_routes.py \
  tests/test_alert_push.py tests/test_auth.py tests/test_rate_limit.py
29 passed in 0.33s

/home/kun/vs_code/au/.venv/bin/python -m pytest -q \
  tests/test_playwright_collector.py tests/test_calculations.py \
  tests/test_collector_manager.py tests/test_price_routes.py tests/test_application.py
33 passed in 0.33s
```

`npm run check` 未能完成：此 worktree 及其上级项目目录没有可解析的 React/Vite
依赖（例如 `react`、`axios`、`vitest`）。未安装依赖或联网。它先暴露了 TypeScript 6
对既有 `baseUrl` 配置的弃用错误，已通过 `ignoreDeprecations: "6.0"` 消除；其余错误
均为缺失模块，尚未能验证前端类型检查。

## 未解决项

- React SPA 目前没有被 Flask 或 Docker 构建/托管：Docker 镜像只运行 Python，页面蓝图
  渲染 Jinja 模板。将 SPA 接入生产构建需要单独确定静态构建与部署入口，未在本次修改。
- 未连接实际 MySQL/浏览器/外部通知服务；本次仅使用离线 mock/fake 测试，未调用网络
  API、未部署或重启服务。
