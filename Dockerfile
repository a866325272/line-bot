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
COPY requirements.txt requirements.txt

ARG EPA_TOKEN
ARG CWA_TOKEN
ARG ACCESS_TOKEN
ARG SECRET
ARG OPENAI_TOKEN
ARG GOOGLE_APPLICATION_CREDENTIALS
ARG LOG_PATH
ARG GMAP_API_KEY
ARG JWT_SECRET_KEY

ENV EPA_TOKEN ${EPA_TOKEN}
ENV CWA_TOKEN ${CWA_TOKEN}
ENV ACCESS_TOKEN ${ACCESS_TOKEN}
ENV SECRET ${SECRET}
ENV OPENAI_TOKEN ${OPENAI_TOKEN}
ENV GOOGLE_APPLICATION_CREDENTIALS ${GOOGLE_APPLICATION_CREDENTIALS}
ENV LOG_PATH ${LOG_PATH}
ENV GMAP_API_KEY ${GMAP_API_KEY}
ENV JWT_SECRET_KEY ${JWT_SECRET_KEY}

RUN pip3 install -r requirements.txt &&\
    apt-get update && apt-get install -y fonts-wqy-zenhei &&\
    rm -rf /var/lib/apt/lists/* /root/.cache/matplotlib/* &&\
    mkdir -p /var/log/line-bot

# Copy application code
COPY app.py app.py
COPY firestore.py firestore.py
COPY gcs.py gcs.py
COPY gss.py gss.py
COPY lma.py lma.py
COPY exceptions.py exceptions.py
COPY middleware/ middleware/
COPY services/ services/
COPY api/ api/

# Copy Vue build output
COPY --from=frontend-build /app/dist ./dist

EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--timeout", "120", "app:app"]
