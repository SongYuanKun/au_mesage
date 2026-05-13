# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
