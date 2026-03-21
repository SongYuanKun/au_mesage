# 贡献指南

感谢你对本项目的关注和贡献！请在提交 issue 或 PR 前先阅读本指南，能让社区协作更顺畅。

## 本地开发与运行

1. 克隆仓库并进入目录：

```bash
git clone https://github.com/SongYuanKun/au_mesage.git
cd au_mesage
```

2. 创建 Python 虚拟环境并安装依赖：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. （可选）若启用 `ENABLE_PLAYWRIGHT=true`，需安装 Playwright 浏览器：

```bash
playwright install chromium
```

4. 配置环境变量并初始化数据库：

```bash
cp .env.example .env
# 编辑 .env 填入实际配置
mysql -h localhost -u root -p price_data < scripts/init.sql
```

5. 运行应用：

```bash
python src/app.py
```

## 代码风格与检查

- 使用 `black` 格式化代码（建议）：`black .`
- 使用 `flake8` 检查静态问题（可选）：`flake8 src`

请在提交 PR 前确保代码通过基本的静态检查并附带必要的说明。

## 提交与 PR 流程

- 使用 feature 分支（如 `feature/add-readme` 或 `fix/mysql-pool`）。
- 提交信息应简洁明了：`type(scope): summary`（例如 `fix(mysql): handle reconnect`）。
- 提交 PR 时请描述变更目的、测试步骤与相关 issue（若有）。

## Issue 模板建议

当你提交 issue 时，请尽量包含：
- 问题描述
- 重现步骤
- 环境信息（Python 版本、OS、MySQL 版本）
- 相关日志或错误堆栈

---

如果你有任何疑问或需要协助，欢迎在 GitHub 上创建 issue。谢谢！
