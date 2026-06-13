FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 5002
CMD ["gunicorn", "--bind", "0.0.0.0:5002", "--workers", "1", "--threads", "4", "--timeout", "0", "app:app"]
