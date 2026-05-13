# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.1] - 2026-05-13

### Added
- **[FR-SVC-002]** Add unique key `uk_price_data` to `price_data` table for idempotency.
- **[FR-SVC-002]** Implement `INSERT IGNORE` for data duplication prevention during collector writes.
- **[FR-SVC-001]** Implement exponential backoff and circuit breaker (degraded state) in base collector.

### Fixed
- **[FR-UI-010]** Optimize SSE subscription `/api/price-alert/subscribe` to use `api_ttl_cache` to drastically reduce database polling overhead per connected client.
