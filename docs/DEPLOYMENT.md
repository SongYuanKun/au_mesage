# 部署说明

## GTR 生产环境（内网 / 公网）

| 场景 | SSH |
|------|-----|
| 局域网直连 | `ssh gtr` |
| 外网经阿里云 2222 转发 | `ssh gtr-pub` |

- **代码目录**：`/home/kun/vs_code/au`（远端 Git 远程名常为 `github`）
- **编排**：根目录 `docker-compose.yml`，容器名 **`my-au`**，端口 **`8083`**
- **数据库**：外部 MySQL（`.env` 中 `MYSQL_HOST` 等），**不在** `docker-compose.yml` 内起库

### 日常更新（代码已 push 到 `main`）

在 GTR 上执行：

```bash
cd ~/vs_code/au
git pull github main
docker compose up --build -d
curl -sf http://127.0.0.1:8083/api/health
```

### 首次启用认证 / 管理端（v0.6.0+）

1. **数据库迁移**（在能连生产库的环境执行一次）：

```bash
mysql -h "$MYSQL_HOST" -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" \
  < scripts/migrations/002_admin_auth_audit.sql
```

2. **后端 `.env`**（勿提交 Git）：

```env
AUTH_ENABLED=true
AUTH_ADMIN_TOKEN=<强随机串>
# 可选
AUTH_OPS_TOKEN=
```

3. **前端构建**（若使用 React SPA 且需登录页/管理页）：

```env
VITE_AUTH_ENABLED=true
```

构建后由 Flask 或静态托管提供；`AUTH_ENABLED=false` 时行为与旧版一致（公开 API）。

4. 重启应用容器后验证：

```bash
curl -s http://127.0.0.1:8083/api/health
# 启用认证后
curl -s -H "Authorization: Bearer $AUTH_ADMIN_TOKEN" http://127.0.0.1:8083/api/auth/me
```

### 本地 Docker（仅应用 + 外部 MySQL）

见 [README.zh-CN.md](../README.zh-CN.md) 方式 A；宿主机 MySQL 时使用 `MYSQL_HOST=host.docker.internal`。

## 展示层（Koen 视觉）

生产站点页面由 **Flask 模板**（`templates/`）+ **静态样式**（`static/css/`）渲染，与仓库内 React SPA（`src/`）独立。

- 设计令牌：`static/css/koen-tokens.css`（Slate + Indigo，与 [Koen 工具箱](https://tools.songyuankun.top) / 内容战略仓库 `koen-content-strategy` 一致）
- 样式入口：`static/css/main.css`（`@import` tokens）
- 共享片段：`templates/_nav.html`、`templates/_footer.html`

更新模板或 CSS 后需 **重建 Docker 镜像**（`docker compose up --build -d`），否则 GTR 仍服务旧静态资源。

## CI 与 RTM

- GitHub Actions：`.github/workflows/python-app.yml`（pytest、RTM 校验、Vitest JUnit/coverage artifacts）
- 高优需求追溯：`docs/SRS/rtm_refs.yml`，校验：`python tools/rtm_traceability_check.py`
