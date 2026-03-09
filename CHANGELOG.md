# Changelog

本项目所有重要变更都会记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [1.1.0] - 2026-03-07

### 新增
- 网站可用性检测机制
- 随机刷新与用户行为模拟，降低被反爬检测的风险

### 修复
- 时间获取修正为北京时间（UTC+8）

## [1.0.0] - 2025-12-25

### 新增
- 基于 Playwright 的贵金属价格自动采集（黄金、白银）
- Flask REST API：最新价格、历史数据、价格计算、健康检查
- SSE 价格到达推送功能（`/api/price-alert/subscribe`）
- ECharts 实时价格趋势图表
- 内存缓冲 + 周期性批量写入数据库
- Docker 容器化部署支持
- MySQL 数据持久化（连接池 + 批量插入优化）
- 自定义 JSON 序列化（Decimal、datetime 支持）
- CI 工作流（black + flake8 + 语法检查）
- 完整的项目文档和贡献指南
