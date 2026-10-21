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
- Playwright 在页面关闭、断连和连续失败后继续重建浏览器并指数退避；缺失选择器、`--`、
  `—` 与零值报价均作为缺失行跳过，不再写入伪 0 价格或产生每分钟 ERROR。
- 文件日志改为 10 MiB、保留 5 份的轮转日志。金银比查询只允许同一来源、币种和
  国内/国际市场口径的金银数据配对。
- React API 客户端改为匹配后端扁平的 `calculate/history` 字段和
  `{success, channels}` 提醒渠道响应；首页旧模板在国际 `USD/oz` 报价时只在获得
  USD/CNY 并切换到人民币/克后计算，否则明确拒绝计算。
- Analysis 页明确展示“购买价差”：购买价高于市场价为红色成本差，购买价低于市场价为
  绿色节省，避免将价差误标为盈亏。数据源 priority 现在决定启用源的启动顺序
  （较小优先级先启动），不宣称它会选择已写入的市场价格。
- React SPA 构建产物由 Docker 多阶段构建复制到 Flask `static/spa`，并由 `/app` 托管；
  `/` 仍为旧 Jinja 首页，SPA 回退不会匹配 `/api/*`。`/app/runtime-config.js` 在 SPA
  启动前提供当前 Flask 进程的 `AUTH_ENABLED`，消除 Docker 镜像构建期与运行期的认证漂移。
- SPA 的未登录角色守卫跳转到 `/app/login`，而不是不存在的根路径 `/login`。
- Playwright 核心买入/卖出报价有效但最高价列缺失或为 `--` 时，写入 `NULL` 最高价；
  不再把缺失值伪造成 `0`。

## 验证

```text
/home/kun/vs_code/au/.venv/bin/python -m pytest -q \
  tests/test_health.py tests/test_app_factory.py tests/test_alert_routes.py \
  tests/test_alert_push.py tests/test_auth.py tests/test_rate_limit.py
29 passed in 0.33s

/home/kun/vs_code/au/.venv/bin/python -m pytest -q
126 passed in 0.75s
```

此前缺少完整前端依赖；用户后续明确授权按锁文件在隔离 worktree 安装，现已完成。
`npm run build`（TypeScript + Vite）通过；`npm test` 共 12 个文件、49 个测试通过。
实际构建发现并修复提醒渠道响应的可选 message 类型；业务拒绝不再被误判为网络错误重试。
App 测试使用生产路由 basename `/app`。构建仅有 runtime-config 脚本与大 chunk 警告。

## 未解决项

个人站报价契约补充：`/api/price-overview` 原本就是公开概览；现在其新鲜和缓存响应
均声明仅允许 `https://koen.songyuankun.top` 跨域读取，不反射任意来源，也不允许跨域
携带凭据。其他 API 不增加跨域头，鉴权开启时导出接口仍返回 401。后端全套已通过
`129 passed`，另有隔离缓存回归覆盖首次查询与复用响应。公网请求因当前环境 DNS
解析失败未能验证，真实浏览器跨域联调仍未完成。

开发代理补充：Vite 同时代理 `/api` 与 `/app/runtime-config.js`，默认目标为 Flask
开发入口的 `http://127.0.0.1:8083`，可用服务端变量 `AU_API_ORIGIN` 覆盖。这样开发
界面也读取后端运行时鉴权配置，而不是缺失脚本后误以为未启用鉴权。已静态复核代理
路径、后端端口和 README 引用，并通过 `git diff --check`；前端类型与生产构建现已通过；尚未启动真实浏览器联调。

- React SPA 通过 `/app` 单独托管，旧 Jinja 首页保留在 `/`；SPA 回退仅匹配 `/app`，
  不会吞掉 `/api` 的 JSON 404。`/app/login` 是 Token 登录入口，`/app/admin/sources`
  仍受前端角色守卫保护；构建和类型检查已在本轮授权安装依赖后通过。
- 未连接实际 MySQL/浏览器/外部通知服务；本次仅使用离线 mock/fake 测试，未调用网络
  API、未部署或重启服务。
