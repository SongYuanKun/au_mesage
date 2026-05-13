# 发布报告与回滚方案 (Release Report)

**版本号**: v0.3.1
**发布日期**: 2026-05-13
**分支信息**: `feature/top-priority-fixes` -> `main`

## 1. 变更清单 (Changelog)

本次发布包含 3 个高优先级（Must）需求的修复与增强：

- **[FR-SVC-002] 数据标准化与入库 (去重)**: 为 `price_data` 表增加联合唯一键 `uk_price_data`，并将后端写入语句调整为 `INSERT IGNORE`，解决了同时间点多次抓取导致的数据重复写入问题。
- **[FR-SVC-001] 多数据源采集调度与容错**: 为基础采集器（`BaseCollector`）引入容错机制。新增连续失败计数器与基于指数退避的重试策略（最大退避 1 小时），当失败达 5 次后标记为降级状态，避免对第三方接口产生雪崩式调用并触发封禁。
- **[FR-UI-010] SSE 连接管理优化**: 优化了 `/api/price-alert/subscribe` 接口中无限循环轮询数据库最新价格的逻辑，改为优先从 `api_ttl_cache` 获取，极大降低了单实例下的数据库连接与查询压力。

## 2. 质量验证 (Quality Assurance)

- **单元测试与集成测试**: 
  - 针对新增的容错逻辑、SSE 推送逻辑及数据去重入库编写了单测用例。
  - 测试套件全量执行通过（`53 passed`）。
  - **核心业务模块代码覆盖率（`src/collectors/base.py`, `src/routes/api/alert_routes.py`, `src/db/price_writer.py`）均已达到或超过 80%**。
- **静态分析**: 
  - 运行 `ruff check src tests` 无报错。
  - 符合团队代码规范（未引入未使用的依赖或未规范格式化的代码）。
- **自动化流与文档**:
  - `docs/SRS/requirements.yml`、`CHANGELOG.md` 与 RTM 均已更新。
  - CI Pipeline 预演无异常。

## 3. 回滚方案 (Rollback Plan)

若部署到生产环境后发现严重故障（如：采集器无法恢复、CPU 100%），请按以下步骤回滚：

1. **代码回滚**:
   ```bash
   git checkout main
   git revert -m 1 HEAD
   git push origin main
   ```
2. **数据库兼容性**:
   - 本次变更引入了新的联合唯一索引 `uk_price_data`，**向下兼容** 旧版代码（旧代码的 `INSERT INTO` 遇到重复数据会抛出 Duplicate Key 异常并被异常处理捕获，不会阻塞整体系统，仅会在日志中产生报错）。
   - 若必须移除索引：
     ```sql
     ALTER TABLE price_data DROP INDEX uk_price_data;
     ```
3. **重新部署**:
   - 触发 CI/CD 重新构建并拉起最新容器即可恢复上一稳定版本 `v0.3.0`。
