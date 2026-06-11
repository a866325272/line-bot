# Stage 1: Build Vue frontend
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python app
FROM python:3.9.16-slim

WORKDIR /app

# Build-time secrets (CI 注入)
ARG EPA_TOKEN CWA_TOKEN ACCESS_TOKEN SECRET OPENAI_TOKEN \
    GOOGLE_APPLICATION_CREDENTIALS LOG_PATH GMAP_API_KEY JWT_SECRET_KEY

ENV EPA_TOKEN=${EPA_TOKEN} \
    CWA_TOKEN=${CWA_TOKEN} \
    ACCESS_TOKEN=${ACCESS_TOKEN} \
    SECRET=${SECRET} \
    OPENAI_TOKEN=${OPENAI_TOKEN} \
    GOOGLE_APPLICATION_CREDENTIALS=${GOOGLE_APPLICATION_CREDENTIALS} \
    LOG_PATH=${LOG_PATH} \
    GMAP_API_KEY=${GMAP_API_KEY} \
    JWT_SECRET_KEY=${JWT_SECRET_KEY}

# 系統依賴（幾乎不變，放最前面最大化 cache）
RUN apt-get update && \
    apt-get install -y --no-install-recommends fonts-wqy-zenhei && \
    rm -rf /var/lib/apt/lists/* && \
    mkdir -p /var/log/line-bot

# Python 依賴（requirements.txt 變更頻率低於程式碼）
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# 應用程式碼
COPY *.py ./
COPY handlers/ handlers/
COPY middleware/ middleware/
COPY services/ services/
COPY api/ api/

# Vue build output
COPY --from=frontend-build /app/dist ./dist

EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--timeout", "120", "app:app"]
