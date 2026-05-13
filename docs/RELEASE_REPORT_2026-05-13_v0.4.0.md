# 发布报告 — v0.4.0（2026-05-13）

## 范围摘要

- 交付工程化门禁：GitHub Actions 前端流水线、Vitest 覆盖率、API 文档。
- 运行时行为无破坏性变更预期；数据库与部署拓扑不变（仍见 `docker-compose.yml` 外部 MySQL 约定）。

## 构建与测试结果（本地/CI 等价命令）

```bash
PYTHONPATH=src pytest tests/ -q
npm run lint && npm run check && npm test -- --coverage && npm run build
```

## 回滚方案

1. **代码**：将 `main` 回退到上一标签或提交（例如包含 `0.3.1` 变更记录的提交），重新部署。
2. **容器**：在部署目录执行 `git checkout <previous_commit> && docker compose up --build -d`（与既有 `my-au` 流程一致）。
3. **数据库**：本版本未引入迁移脚本；无需库结构回滚。若曾单独执行 SQL，请按变更清单逆向操作（本次无）。

## 已知限制

- 覆盖率「分支」阈值设为 70%：图表 Tooltip 与部分错误分支组合较多，后续可通过契约测试或导出纯函数单测抬升。
