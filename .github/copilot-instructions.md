pip install -r requirements.txt
docker build -t my-au .;
docker run -p 8083:8083 --env-file .env my-au
docker-compose up --build

---
# Copilot/AI Agent 项目专用开发说明

## 架构与数据流
- 服务分为数据采集（`src/playwright_collector.py`，Playwright 线程后台抓取）与 HTTP API（Flask，`src/app.py`+`src/route.py`）。
- 数据流：Playwright → 内存 data_buffer → 定时 batch_insert_data 写入 MySQL（表 `price_data`）→ Flask API 查询 MySQL → 前端（`templates/index.html`）。
- 配置集中于 `config.ini`，支持环境变量覆盖。容器部署见 `Dockerfile`、`docker-compose.yml`。

## 关键文件/目录
- `src/app.py`：主入口，启动采集器和 Flask。
- `src/route.py`：API 路由，所有接口均需返回 `{success: bool, data/error: ...}`。
- `src/mysql_manager.py`：MySQL 连接池（池名 price_pool），所有查询/写入均用参数化，表仅 `price_data`。
- `src/playwright_collector.py`：采集线程，默认 headless，调试可设为 False。
- `src/CustomJSONEncoder.py`：Flask JSONProvider，自动处理 Decimal/datetime。
- `templates/index.html`：前端交互与 ECharts。

## 项目约定与自动化注意
- SQL 查询必须包含 `recycle_price > 0` 过滤。
- data_type 仅允许 `黄 金`、`白 银`（前后空格），前后端/数据库一致。
- 新增 API 必须复用标准响应格式，异常统一 try/except 并日志。
- 连接池只初始化一次，禁止高频新建。
- 路由模板目录为 `../templates`，运行/编辑时工作目录为仓库根。
- JSON 输出依赖 `CustomJSONProvider`，返回类型需兼容前端解析。

## 开发/调试常用命令
- 本地：`python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && python src/app.py`
- Playwright 浏览器安装：`playwright install && playwright install chromium`
- Docker 构建/运行：`docker-compose up --build` 或 `docker build -t my-au . && docker run -p 8083:8083 --env-file .env my-au`
- 数据库初始化：`mysql -h <host> -u <user> -p<password> <database> < scripts/init.sql`

## 扩展与自定义
- 新采集类型：前端按钮+采集器解析+data_type 字段，无需改表。
- 新 API：`route.py` 注册路由，`mysql_manager.py` 实现查询，响应结构与异常处理需一致。

## 常见调试/排查
- Playwright 选择器失效：`headless=False` 本地调试，F12 检查。
- 日志：`price_service.log`（根目录），INFO/ERROR 级别。
- 采集/数据库异常：优先查日志和连接池状态。

## AI 代理限制
- 仅操作 `price_data` 表，禁止假设/创建其他表或字段。
- 禁止移除 recycle_price > 0 过滤。
- data_type 拼写必须精确。
- 禁止在 API 路径新建连接池。
- API 响应结构不可破坏。

---
如需补充说明或遇到不明确约定，请优先参考 `README.md` 或直接询问维护者。
- 在容器中运行时：确保已执行 `playwright install` 或在 Dockerfile 中安装浏览器二进制；容器运行时需要 `--no-sandbox` 等参数（代码中已设置）。
