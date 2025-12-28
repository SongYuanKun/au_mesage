# Docker 部署脚本说明 🐳

本目录包含用于以“停止旧容器并用最新代码/镜像覆盖部署”流程的脚本。

文件列表：
- `update.sh`：适用于类 Unix（Linux/macOS）的部署脚本。
- `update.ps1`：适用于 Windows PowerShell 的部署脚本。

使用方式：
1. 确保本地代码是你想部署的版本（例如：`git pull` 或切换分支）。
2. 在项目根目录执行：
   - Linux/macOS：`./scripts/update.sh`
   - Windows PowerShell：`.\scripts\update.ps1`

脚本步骤：
- `docker-compose down --remove-orphans` 停止并移除旧容器
- `docker-compose build --no-cache --pull` 全量构建镜像
- `docker-compose up -d --force-recreate --remove-orphans` 后台启动并强制重建容器
- 清理未使用的镜像（`docker image prune -f`）

提示：
- 若在 CI 中执行，可直接调用这些脚本以确保部署一致性。
- 如果你希望在更新前先拉取远端代码，可在脚本中添加 `git pull` 步骤。