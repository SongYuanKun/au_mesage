# 使用官方 Python 轻量级镜像
FROM python:3.11-slim-bookworm

# 设置工作目录
WORKDIR /app

# 更新包索引，安装必需的系统依赖（简化版本）
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    tzdata \
    # Playwright 浏览器依赖（最小必需）
    libnss3 \
    libnspr4 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxss1 \
    libasound2 \
    libatspi2.0-0 \
    libgtk-3-0 \
    libgdk-pixbuf2.0-0 \
    libxcursor1 \
    libxi6 \
    libxrender1 \
    libxext6 \
    libx11-6 \
    tini \
    bash \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 复制 requirements.txt 并安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# 复制项目文件
COPY . .

# 安装 Playwright 浏览器
RUN playwright install chromium

# 设置环境变量
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Shanghai

# 暴露端口
EXPOSE 8083

# 入口与启动命令
CMD ["python", "src/app.py"]