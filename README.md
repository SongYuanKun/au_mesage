# 贵金属价格数据采集与分析平台

一个基于 **Playwright** 自动化采集、**Flask** API 服务、**MySQL** 数据存储的贵金属（黄金、白银）实时价格监测系统。支持数据采集、历史查询、价格计算和可视化展示，提供 Docker 容器化部署方案。

## 📋 项目概览

本项目是一个完整的金属价格采集和服务平台，包含以下核心功能：

- **实时采集**：通过 Playwright 无头浏览器自动采集目标网站的黄金、白银等贵金属价格
- **数据持久化**：采用 MySQL 数据库存储价格历史，支持批量插入优化
- **REST API**：提供灵活的 Flask API，支持查询最新价格、历史数据、价格计算等
- **可视化展示**：内置 ECharts 图表，实时展示价格趋势
- **容器化部署**：提供 Dockerfile 和 docker-compose 配置，一键启动服务

### 核心特性

✅ 后台自动采集（线程化，无阻塞）  
✅ 内存缓冲 + 周期性批量写入（30 秒缓冲，高效数据库操作）  
✅ 支持多种数据类型（黄金、白银，易于扩展）  
✅ JSON 序列化优化（Decimal、datetime 自动转换）  
✅ 完整的错误处理与日志记录  
✅ Docker 容器化（含浏览器依赖配置）  

---

## 🏗️ 架构设计

```
┌─────────────────────────────────────────────────────┐
│         Web Browser (Playwright)                    │
│    自动采集目标网站实时价格                          │
└────────────────────┬────────────────────────────────┘
                     │ 采集数据
                     ▼
┌─────────────────────────────────────────────────────┐
│   PlaywrightDataCollector (后台线程)                │
│   - 每分钟刷新一次                                  │
│   - 每 30 秒保存缓冲区                              │
│   - 内存缓冲: data_buffer[]                         │
└────────────────────┬────────────────────────────────┘
                     │ batch_insert_data()
                     ▼
┌─────────────────────────────────────────────────────┐
│      MySQL Database (price_data 表)                 │
│   ┌─────────────────────────────────────────────┐  │
│   │ trade_date | trade_time | data_type |       │  │
│   │ real_time_price | recycle_price | ...       │  │
│   └─────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────┘
                     │ SQL Query
                     ▼
┌─────────────────────────────────────────────────────┐
│    Flask API Routes (REST Endpoints)                │
│   - /api/latest-price        (最新价格)             │
│   - /api/recent-history      (历史数据)             │
│   - /api/calculate           (价格计算)             │
│   - /api/health              (健康检查)             │
│   - /api/price-alert/subscribe (价格到达推送, SSE)  │
└────────────────────┬────────────────────────────────┘
                     │ JSON Response
                     ▼
┌─────────────────────────────────────────────────────┐
│   Web Frontend (HTML + JavaScript + ECharts)        │
│   - 实时价格展示                                    │
│   - 价格趋势图表                                    │
│   - 价格计算器                                      │
└─────────────────────────────────────────────────────┘
```

---

## 📁 项目结构

```
au/
├── config.ini                    # 配置文件（MySQL、API、Playwright）
├── requirements.txt              # Python 依赖列表
├── Dockerfile                    # Docker 镜像构建文件
├── docker-compose.yml            # Docker Compose 编排配置
├── README.md                     # 本文件
├── .gitignore                    # Git 忽略规则
│
├── src/                          # 源代码目录
│   ├── app.py                    # 应用程序入口，启动采集器和 Flask
│   ├── route.py                  # Flask 路由和 API 端点定义
│   ├── mysql_manager.py          # MySQL 连接池和数据库操作
│   ├── playwright_collector.py   # Playwright 采集器（线程化）
│   ├── CustomJSONEncoder.py      # 自定义 JSON 序列化器
│   └── __pycache__/              # Python 缓存目录
│
├── templates/                    # 前端模板目录
│   └── index.html                # 主页 HTML（包含 ECharts 图表和 JavaScript 逻辑）
│
└── scripts/                      # 脚本目录
    └── init.sql                  # 数据库初始化 SQL
```

---

## 🚀 快速开始

### 前置要求

- **Python 3.8+**
- **MySQL 5.7+** 或 **8.0+**
- **Node.js** 和 **npm**（可选，Docker 已内置）
- **Docker** 和 **Docker Compose**（容器化部署时）

### 本地开发（Windows PowerShell）

#### 1. 克隆仓库

```powershell
git clone https://github.com/SongYuanKun/au_mesage.git
cd au
```

#### 2. 创建虚拟环境

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

#### 3. 安装依赖

```powershell
pip install -r requirements.txt
```

#### 4. 安装 Playwright 浏览器

```powershell
playwright install
playwright install chromium
```

#### 5. 配置数据库

编辑 `config.ini` 文件，修改 MySQL 连接信息：

```ini
[mysql]
host = your_mysql_host        # MySQL 服务器地址
user = your_mysql_user        # MySQL 用户名
password = your_mysql_password # MySQL 密码
database = your_database_name  # 数据库名称

[api]
host = 0.0.0.0                # API 绑定地址
port = 8083                   # API 监听端口

[playwright]
headless = true               # 是否无头运行（true 用于生产环境）
timeout = 30000               # 页面加载超时时间（毫秒）
```

#### 6. 初始化数据库

在 MySQL 中执行 `scripts/init.sql`：

```powershell
# 使用 MySQL 命令行或 GUI 工具执行
mysql -h <host> -u <user> -p<password> <database> < scripts/init.sql
```

或在 MySQL 客户端中直接运行：

```sql
CREATE TABLE IF NOT EXISTS price_data (
  id INT AUTO_INCREMENT PRIMARY KEY,
  trade_date DATE NOT NULL,
  trade_time TIME NOT NULL,
  data_type VARCHAR(50) NOT NULL,
  real_time_price DECIMAL(10, 4) DEFAULT 0,
  recycle_price DECIMAL(10, 4) DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_type_date (data_type, trade_date),
  INDEX idx_created_at (created_at)
);
```

#### 7. 启动应用

```powershell
python src/app.py
```

应用将在以下地址启动：
- **Web 界面**：http://localhost:8083
- **API 基础 URL**：http://localhost:8083/api

查看日志文件：

```powershell
# Windows PowerShell
Get-Content price_service.log -Tail 50 -Wait
```

---

## 🐳 Docker 容器化部署

### 方式 1：使用 docker-compose（推荐）

```powershell
docker-compose up --build
```

应用将在 http://localhost:8083 启动。

### 方式 2：手动构建和运行

#### 构建镜像

```powershell
docker build -t au-price-collector .
```

#### 创建 .env 文件

```env
MYSQL_HOST=your_mysql_host
MYSQL_USER=your_mysql_user
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=your_database_name
API_HOST=0.0.0.0
API_PORT=8083
```

#### 运行容器

```powershell
docker run -p 8083:8083 `
  --env-file .env `
  --name au-collector `
  au-price-collector
```

#### 停止容器

```powershell
docker stop au-collector
docker rm au-collector
```

---

## 📡 API 文档

### 基础信息

- **基础 URL**：`http://localhost:8083`
- **响应格式**：JSON
- **超时设置**：30 秒

### 标准响应格式

#### 成功响应（HTTP 200）

```json
{
  "success": true,
  "data": {
    "trade_date": "2025-11-24",
    "trade_time": "10:30:00",
    "data_type": "黄 金",
    "real_time_price": 585.50,
    "recycle_price": 575.30
  }
}
```

#### 失败响应（HTTP 4xx/5xx）

```json
{
  "success": false,
  "error": "错误描述信息"
}
```

### API 端点

#### 1. 获取最新价格

**端点**：`GET /api/latest-price`

**参数**（可选）：
- `data_type` (string)：数据类型，如 `黄 金`、`白 银`（若不指定则返回所有类型的最新价格）

**请求示例**：

```powershell
# 获取所有类型的最新价格
curl -Uri "http://localhost:8083/api/latest-price" -Method GET | ConvertFrom-Json

# 获取特定类型（黄金）的最新价格
curl -Uri "http://localhost:8083/api/latest-price?data_type=黄%20金" -Method GET | ConvertFrom-Json
```

**响应示例**：

```json
{
  "success": true,
  "data": [
    {
      "trade_date": "2025-11-24",
      "trade_time": "14:30:00",
      "data_type": "黄 金",
      "real_time_price": 585.50,
      "recycle_price": 575.30
    },
    {
      "trade_date": "2025-11-24",
      "trade_time": "14:30:00",
      "data_type": "白 银",
      "real_time_price": 8.20,
      "recycle_price": 7.95
    }
  ]
}
```

---

#### 2. 获取历史价格数据（图表用）

**端点**：`GET /api/recent-history`

**参数**（必需）：
- `data_type` (string)：数据类型，如 `黄 金`、`白 银`

**查询限制**：最多返回最近 30 条数据点（用于前端图表展示）

**请求示例**：

```powershell
curl -Uri "http://localhost:8083/api/recent-history?data_type=黄%20金" -Method GET | ConvertFrom-Json
```

**响应示例**：

```json
{
  "success": true,
  "data": [
    {
      "trade_date": "2025-11-24",
      "trade_time": "10:00:00",
      "data_type": "黄 金",
      "real_time_price": 580.00,
      "recycle_price": 570.00
    },
    {
      "trade_date": "2025-11-24",
      "trade_time": "10:30:00",
      "data_type": "黄 金",
      "real_time_price": 582.50,
      "recycle_price": 572.50
    },
    ...
  ]
}
```

---

#### 3. 价格计算接口

**端点**：`POST /api/calculate`

**请求体**（JSON）：

```json
{
  "product_price": 500,      // 商品单价（元/克）
  "weight": 10,              // 重量（克）
  "data_type": "黄 金"       // 数据类型
}
```

**请求示例**：

```powershell
$body = @{
  product_price = 500
  weight = 10
  data_type = "黄 金"
} | ConvertTo-Json

curl -Uri "http://localhost:8083/api/calculate" `
  -Method POST `
  -Headers @{"Content-Type"="application/json"} `
  -Body $body | ConvertFrom-Json
```

**响应示例**：

```json
{
  "success": true,
  "data": {
    "total_price": 5000,
    "product_price": 500,
    "weight": 10,
    "data_type": "黄 金"
  }
}
```

---

#### 4. 健康检查

**端点**：`GET /api/health`

**用途**：检查服务状态和数据库连接

**请求示例**：

```powershell
curl -Uri "http://localhost:8083/api/health" -Method GET | ConvertFrom-Json
```

**响应示例**：

```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2025-11-24T14:30:00"
}
```

---

## 🔧 配置说明

### config.ini 详细配置

```ini
[mysql]
host = your_mysql_host             # MySQL 服务器地址
user = your_mysql_user             # MySQL 用户名
password = your_mysql_password     # MySQL 密码（生产环境建议使用环境变量）
database = your_database_name      # 数据库名

[api]
host = 0.0.0.0                     # Flask API 绑定地址（0.0.0.0 表示所有接口）
port = 8083                        # Flask API 监听端口

[playwright]
headless = true                    # 是否无头运行（true=生产环境，false=调试模式）
timeout = 30000                    # 页面加载超时时间（毫秒）
```

### 环境变量支持

支持通过环境变量覆盖配置：

```powershell
$env:MYSQL_HOST = "your-host"
$env:MYSQL_USER = "your-user"
$env:MYSQL_PASSWORD = "your-password"
$env:MYSQL_DATABASE = "your-db"
$env:API_HOST = "0.0.0.0"
$env:API_PORT = "8083"

python src/app.py
```

---

## 📊 数据库模式

### price_data 表结构

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | INT | PRIMARY KEY, AUTO_INCREMENT | 主键，自增 |
| `trade_date` | DATE | NOT NULL | 交易日期 |
| `trade_time` | TIME | NOT NULL | 交易时间 |
| `data_type` | VARCHAR(50) | NOT NULL | 数据类型（黄 金、白 银）|
| `real_time_price` | DECIMAL(10,4) | DEFAULT 0 | 实时价格（元/克） |
| `recycle_price` | DECIMAL(10,4) | DEFAULT 0 | 回收价格（元/克）|
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

### 索引配置

```sql
INDEX idx_type_date (data_type, trade_date)  -- 用于 data_type + trade_date 查询
INDEX idx_created_at (created_at)             -- 用于时间范围查询和排序
```

---

## 🔍 核心模块说明

### 1. app.py（应用入口）

**职责**：
- 初始化日志系统
- 加载配置文件
- 启动 MySQL 管理器
- 启动 Playwright 采集器（后台线程）
- 启动 Flask 应用

**关键函数**：
- `setup_logging()`：配置日志输出到文件和控制台
- `load_config()`：从 `config.ini` 加载配置
- `main()`：应用主入口

**日志文件**：`price_service.log`

```python
# 运行应用
python src/app.py
```

---

### 2. route.py（REST API 路由）

**职责**：
- 定义 Flask 应用和所有路由
- 处理 HTTP 请求和响应
- 调用 MySQLManager 进行数据操作
- 返回 JSON 格式的数据

**关键端点**：
- `GET /`：渲染主页
- `GET /api/latest-price`：获取最新价格
- `GET /api/recent-history`：获取历史价格
- `POST /api/calculate`：计算价格
- `GET /api/health`：健康检查

**特性**：
- 完整的异常处理
- 使用 CustomJSONProvider 处理特殊数据类型
- RESTful API 设计

---

### 3. mysql_manager.py（数据库管理）

**职责**：
- 管理 MySQL 连接池
- 执行数据库查询和插入操作
- 提供数据库接口给其他模块

**关键类**：`MySQLManager`

**关键方法**：
- `get_latest_data(data_type)`：获取特定类型的最新价格
- `get_latest_data_by_type()`：获取所有类型的最新价格
- `get_price_history(data_type, limit=30)`：获取历史价格数据
- `batch_insert_data(data_list)`：批量插入数据
- `get_connection()`：从连接池获取连接

**连接池配置**：
- 池名：`price_pool`
- 默认大小：5 个连接
- 支持自动重连

**查询优化**：
- 使用参数化查询防止 SQL 注入
- 批量插入提高性能
- 索引优化查询速度

---

### 4. playwright_collector.py（数据采集器）

**职责**：
- 使用 Playwright 自动化采集网站数据
- 后台线程持续运行
- 内存缓冲数据，周期性保存到数据库

**关键类**：`PlaywrightDataCollector`

**采集流程**：
1. 启动无头 Chromium 浏览器
2. 定期访问目标网站（每分钟）
3. 解析 HTML 提取价格数据
4. 存储到内存缓冲区 `data_buffer`
5. 每 30 秒调用 `batch_insert_data()` 写入数据库

**关键方法**：
- `start_collection()`：启动采集线程
- `stop_collection()`：停止采集线程
- `collect_data()`：采集数据的主逻辑

**配置参数**：
- `headless=True`：无头运行（生产环境）
- `timeout=30000`：页面加载超时（毫秒）

**调试技巧**：
修改 `headless=False` 可以看到浏览器窗口，便于调试选择器：

```python
# playwright_collector.py 第 27 行
browser = await p.chromium.launch(headless=False)  # 改为 False 用于调试
```

---

### 5. CustomJSONEncoder.py（JSON 序列化）

**职责**：
- 自定义 Flask JSON 编码器
- 将不支持的类型（Decimal、datetime）转换为 JSON 兼容的类型

**支持的转换**：
- `datetime` → ISO 8601 字符串
- `date` → ISO 格式字符串
- `Decimal` → float
- `timedelta` → 秒数

**使用**：

```python
# 在 route.py 中配置
from CustomJSONEncoder import CustomJSONProvider
app.json = CustomJSONProvider(app)
```

---

## 🐛 调试指南

### 1. 检查数据库连接

```powershell
# 使用 MySQL 命令行
mysql -h your_mysql_host -u your_mysql_user -p
# 输入密码后
SELECT COUNT(*) FROM price_data;
```

### 2. 调试 Playwright 选择器

编辑 `playwright_collector.py`，改为有头运行：

```python
# 第 27 行
browser = await p.chromium.launch(headless=False)
```

运行应用，Playwright 会打开浏览器窗口，用 F12 开发者工具检查选择器。

### 3. 查看实时日志

```powershell
# Windows PowerShell - 实时查看日志
Get-Content price_service.log -Tail 50 -Wait

# 或使用 tail 命令（如果已安装）
tail -f price_service.log
```

### 4. 测试 API 端点

```powershell
# 健康检查
curl -Uri "http://localhost:8083/api/health" -Method GET

# 获取最新价格
curl -Uri "http://localhost:8083/api/latest-price" -Method GET

# 获取历史数据
curl -Uri "http://localhost:8083/api/recent-history?data_type=黄%20金" -Method GET
```

### 5. 常见问题排查

| 问题 | 原因 | 解决方案 |
|------|------|--------|
| 无法连接 MySQL | 配置错误或 MySQL 未运行 | 检查 `config.ini` 和 MySQL 服务状态 |
| Playwright 超时 | 页面加载慢或选择器不匹配 | 改为 `headless=False` 调试 |
| JSON 序列化错误 | 返回类型不兼容 | 确保使用 CustomJSONProvider |
| API 返回 404 | 路由未注册 | 检查 `route.py` 中的 `@app.route()` 定义 |
| 采集数据为 0 | 网站 HTML 结构变更 | 检查 CSS 选择器是否仍然有效 |

---

## 📈 数据采集流程详解

### 采集周期

```
启动应用
    ↓
Playwright 采集器启动（后台线程）
    ↓
[每 1 分钟执行一次采集逻辑]
    ├─ 打开浏览器
    ├─ 导航到目标网站
    ├─ 等待页面加载完成
    ├─ 解析 DOM 提取数据
    ├─ 关闭浏览器
    └─ 数据添加到 data_buffer（内存）
    ↓
[每 30 秒执行一次保存逻辑]
    ├─ 检查 data_buffer 是否有数据
    ├─ 批量调用 MySQLManager.batch_insert_data()
    ├─ 数据写入 MySQL price_data 表
    └─ 清空内存缓冲区
    ↓
[无限循环，直到 KeyboardInterrupt]
```

### 性能优化点

✅ **内存缓冲**：减少数据库写入次数  
✅ **批量插入**：使用 `executemany` 提高插入速度  
✅ **后台线程**：采集不阻塞 API 服务  
✅ **连接池**：复用数据库连接，减少连接开销  
✅ **索引优化**：加快查询速度  

---

## 🚢 生产部署

### Docker 部署步骤

#### 1. 构建镜像

```powershell
docker build -t au-price-collector:1.0 .
```

#### 2. 创建 .env 文件（存放敏感信息）

```env
MYSQL_HOST=your-production-mysql-host
MYSQL_USER=production-user
MYSQL_PASSWORD=strong-password-here
MYSQL_DATABASE=production-db
API_HOST=0.0.0.0
API_PORT=8083
```

#### 3. 使用 docker-compose 启动

```powershell
docker-compose up -d
```

#### 4. 查看日志

```powershell
docker-compose logs -f app
```

#### 5. 停止服务

```powershell
docker-compose down
```

### 网络配置

#### 端口映射

```yaml
# docker-compose.yml
ports:
  - "8083:8083"  # 本机 8083 端口映射到容器 8083 端口
```

#### 环境网络访问

如需外部访问，修改 `config.ini`：

```ini
[api]
host = 0.0.0.0      # 绑定到所有网络接口
port = 8083
```

#### 防火墙配置（Windows）

```powershell
# 允许 8083 端口通过防火墙
New-NetFirewallRule -DisplayName "Allow AU Price Service" `
  -Direction Inbound -LocalPort 8083 -Protocol TCP -Action Allow
```

### 监控和维护

#### 检查容器状态

```powershell
docker ps -a  # 查看所有容器

docker stats   # 实时监控容器资源使用
```

#### 查看容器日志

```powershell
docker logs -f my-au              # 查看最新日志
docker logs my-au --tail 100      # 查看最后 100 行
```

#### 进入容器调试

```powershell
docker exec -it my-au /bin/bash
```

---

## 🔐 安全建议

1. **数据库密码**：使用环境变量而非配置文件硬编码
2. **API 认证**：在生产环境添加 API Token 验证（可扩展）
3. **HTTPS**：在生产环境使用 HTTPS（配置反向代理如 Nginx）
4. **日志管理**：定期清理日志文件防止磁盘爆满
5. **数据备份**：定期备份 MySQL 数据库

---

## 📚 扩展与自定义

### 添加新的数据类型

#### 步骤 1：修改前端（templates/index.html）

```html
<!-- 在数据类型选择器中添加新按钮 -->
<button id="typePlatin" data-type="铂 金">铂 金</button>
```

```javascript
// 在 JavaScript 中添加点击监听
document.getElementById('typePlatin').addEventListener('click', () => selectType('铂 金'));
```

#### 步骤 2：修改采集器（src/playwright_collector.py）

更新网站选择器和解析逻辑以支持新数据类型。

#### 步骤 3：数据库

新类型会自动通过 `data_type` 字段区分，无需修改表结构。

### 添加新的 API 端点

在 `src/route.py` 中注册新路由：

```python
@app.route('/api/custom-query', methods=['POST'])
def custom_query():
    """自定义查询示例"""
    try:
        data = request.get_json()
        data_type = data.get('data_type')
        days = data.get('days', 7)
        
        if not data_type:
            return jsonify({'success': False, 'error': '缺少 data_type 参数'}), 400
        
        results = mysql_manager.get_data_last_n_days(data_type, days)
        return jsonify({'success': True, 'data': results})
    except Exception as e:
        logging.error(f"自定义查询错误: {e}")
        return jsonify({'success': False, 'error': '服务器内部错误'}), 500
```

---

## 📝 日志管理

### 日志文件位置

应用会在项目根目录生成 `price_service.log` 文件。

### 日志级别

```
INFO     - 一般信息（启动、采集数据等）
ERROR    - 错误信息（数据库连接失败、采集异常等）
WARNING  - 警告信息（超时、重试等）
```

### 日志格式

```
2025-11-24 10:30:00,123 - root - INFO - 应用启动成功
2025-11-24 10:31:00,456 - root - INFO - 批量插入 5 条数据到数据库
2025-11-24 10:35:00,789 - root - ERROR - 数据库连接失败: Connection refused
```

### 日志查看（PowerShell）

```powershell
# 实时查看（持续跟踪）
Get-Content price_service.log -Tail 50 -Wait

# 搜索错误日志
Select-String "ERROR" price_service.log

# 按日期过滤
Get-Content price_service.log | Select-String "2025-11-24"
```

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

### 本地开发流程

1. Fork 仓库
2. 创建特性分支：`git checkout -b feature/your-feature`
3. 提交更改：`git commit -am 'Add your feature'`
4. 推送到分支：`git push origin feature/your-feature`
5. 提交 Pull Request

### 代码规范

- 遵循 PEP 8 Python 代码规范
- 添加适当的注释和文档字符串
- 确保所有单元测试通过
- 更新 README 文档

---

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

---

## 👤 作者

**宋元昆** (SongYuanKun)

- GitHub：[@SongYuanKun](https://github.com/SongYuanKun)
- 项目地址：[au_mesage](https://github.com/SongYuanKun/au_mesage)

---

## 📞 支持与反馈

如有问题或建议，请：

1. 提交 GitHub Issues
2. 发送邮件反馈
3. 查看 FAQ 部分

---

## 🎯 项目路线图

- [ ] 支持更多数据类型（铂金、钯金等）
- [ ] 添加用户认证系统
- [ ] 实现数据导出功能（Excel、CSV）
- [ ] 添加 WebSocket 实时推送
- [ ] 性能监控面板
- [ ] 多语言支持（English、日本語）
- [ ] 移动端应用
- [ ] 数据分析和预测功能

---

## ❓ FAQ

### Q: 采集数据多久更新一次？
A: 默认每分钟采集一次，每 30 秒保存一次到数据库。可在 `playwright_collector.py` 中修改 `asyncio.sleep()` 的参数。

### Q: 如何修改采集网站？
A: 在 `playwright_collector.py` 顶部修改 `website_url` 和 CSS 选择器，然后根据页面结构调整解析逻辑。

### Q: 数据库备份策略？
A: 建议使用 MySQL 自带的 `mysqldump` 工具或配置主从复制。

### Q: 如何在生产环境中运行？
A: 使用 Docker Compose 或 Kubernetes，配合 Nginx 反向代理和 SSL/TLS 证书。

### Q: 支持数据导出吗？
A: 当前不支持，但可以通过 SQL 查询直接导出。可在路线图中考虑实现此功能。

---

## 📊 性能指标

基于当前配置的参考性能指标：

- **API 响应时间**：< 100ms（最新价格查询）
- **数据库批量插入**：每 30 秒批量写入（通常 1-2 条记录）
- **采集间隔**：1 分钟 / 次
- **内存占用**：约 200-300 MB（含 Chromium）
- **CPU 占用**：采集时 20-30%，空闲时 < 5%

---

**Last Updated**: 2025年11月24日  
**Version**: 1.0.0  
**Status**: ✅ Production Ready
#### 3. 订阅价格到达推送（SSE）

端点：`GET /api/price-alert/subscribe`

参数：
- `data_type` (string)：数据类型，如 `黄 金`、`白 银`
- `target` (number)：目标价格阈值（元/克）
- `op` (string)：比较操作，`gte`（达到或超过）或 `lte`（达到或低于），默认 `gte`
- `auto_close` (bool)：命中后是否自动关闭连接，默认 `true`

响应：`text/event-stream`
- `event: price` 最新价格心跳，数据示例：`{"price": 585.5}`
- `event: alert` 命中阈值时推送一次：`{"price": 585.5, "target": 585.0, "op": "gte"}`
- `event: ping` 保活事件

前端使用示例：

```javascript
const url = `/api/price-alert/subscribe?data_type=黄%20金&target=585.0&op=gte&auto_close=true`;
const es = new EventSource(url);
es.addEventListener('price', ev => console.log('price', JSON.parse(ev.data)));
es.addEventListener('alert', ev => console.log('alert', JSON.parse(ev.data)));
es.onerror = () => console.log('连接错误');
```

注意：SSE 为长连接，建议在不需要时调用 `es.close()` 释放资源。
