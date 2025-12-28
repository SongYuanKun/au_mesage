<# PowerShell 版更新脚本：在 Windows 上运行（需要已安装 Docker & Docker Compose） #>
Set-StrictMode -Version Latest

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Resolve-Path "$here\.."
Set-Location $root

Write-Host "Stopping and removing existing containers..."
docker-compose down --remove-orphans

Write-Host "Building image (no cache, pulling latest base image)..."
docker-compose build --no-cache --pull

Write-Host "Starting containers..."
docker-compose up -d --force-recreate --remove-orphans

Write-Host "Pruning unused images..."
docker image prune -f

Write-Host "Deployment complete."
