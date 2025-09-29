# 使用官方 Python 轻量级镜像作为基础镜像
FROM python:3.9-slim

# 设置容器内的工作目录
WORKDIR /app

# 首先复制依赖文件列表
COPY requirements.txt .

# 然后安装依赖（移除了 -i 链接参数，使用默认 PyPI 源）
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制整个项目结构（确保包含 templates 目录）
COPY . .

# 设置环境变量，确保应用在生产模式下运行
ENV FLASK_APP=src/app.py
ENV FLASK_ENV=production

# 声明容器运行时监听的端口
EXPOSE 8083

# 定义容器启动时执行的命令
CMD ["python", "src/app.py"]