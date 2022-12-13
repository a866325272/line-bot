FROM python:3.9.16-slim
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY . .
CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]
# CMD exec gunicorn --bind :5000 --workers 1 --threads 8 --timeout 0 app:app
