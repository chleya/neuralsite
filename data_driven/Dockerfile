# =============================================================================
# NeuralSite Data-Driven Dockerfile
# =============================================================================

FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖 (仅保留必需的)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY dd_requirements ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY data_driven/ ./data_driven/
COPY packages/ ./packages/

EXPOSE 8000

CMD ["uvicorn", "data_driven.interfaces.rest:app", "--host", "0.0.0.0", "--port", "8000"]
