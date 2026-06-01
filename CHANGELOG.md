# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.6.0] - 2026-06-01

### Added

- **[FR-AUTH-001]** Bearer Token 认证（`AUTH_ENABLED`）；保护 `/api/admin/*` 与导出接口；前端登录与路由守卫（`VITE_AUTH_ENABLED`）。
- **[FR-ADM-001]** 数据源配置 CRUD、优先级、版本回滚；采集健康度统计；`AdminSources` 管理页。
- **[SEC-002]** 审计日志（导出、配置变更、登录/403）；`GET /api/admin/audit`；入库脱敏。
- **[NFR-MNT-001]** `docs/SRS/rtm_refs.yml`、RTM 校验脚本、CI 测试报告 artifacts（JUnit/coverage）。
- **迁移**：`scripts/migrations/002_admin_auth_audit.sql`。
- **文档**：`docs/DEPLOYMENT.md`（含 GTR 部署步骤）。

### Changed

- `docs/API.md` 补充认证与管理端接口说明。

## [0.4.0] - 2026-05-13

### Added
- **CI**：新增 `frontend` Job（Node 20）：`eslint src`、`tsc`、`vitest --coverage`、`vite build`。
- **测试**：补充 `Home`、`PriceTrendChart`、`GoldSilverRatioChart`、`App`、`useTheme`、`Empty`、`cn` 等用例；`@vitest/coverage-v8` 与覆盖率阈值（行/语句/函数 ≥80%，分支 ≥70% 并附说明）。
- **文档**：新增 `docs/API.md`，与当前 Flask 路由对齐。

### Fixed
- **Vitest**：在 `src/test/setup.ts` 为 `window.matchMedia` 提供默认 mock，避免主题 store 在 jsdom 下导入失败。

### Changed
- **ESLint**：`lint` 脚本改为仅检查 `src/`，并忽略 `coverage`、`docs/**`，避免误扫生成物。

## [0.3.1] - 2026-05-13

### Added
- **[FR-SVC-002]** Add unique key `uk_price_data` to `price_data` table for idempotency.
- **[FR-SVC-002]** Implement `INSERT IGNORE` for data duplication prevention during collector writes.
- **[FR-SVC-001]** Implement exponential backoff and circuit breaker (degraded state) in base collector.

### Fixed
- **[FR-UI-010]** Optimize SSE subscription `/api/price-alert/subscribe` to use `api_ttl_cache` to drastically reduce database polling overhead per connected client.
