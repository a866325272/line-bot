FROM python:3.9.16-slim
RUN mkdir -p /var/log/line-bot
WORKDIR /app
COPY requirements.txt requirements.txt

ARG EPA_TOKEN
ARG CWB_TOKEN
ARG ACCESS_TOKEN
ARG SECRET
ARG OPENAI_TOKEN
ARG GOOGLE_APPLICATION_CREDENTIALS
ARG LOG_PATH

ENV EPA_TOKEN ${EPA_TOKEN}
ENV CWB_TOKEN ${CWB_TOKEN}
ENV ACCESS_TOKEN ${ACCESS_TOKEN}
ENV SECRET ${SECRET}
ENV OPENAI_TOKEN ${OPENAI_TOKEN}
ENV GOOGLE_APPLICATION_CREDENTIALS ${GOOGLE_APPLICATION_CREDENTIALS}
ENV LOG_PATH ${LOG_PATH}

RUN pip3 install -r requirements.txt
RUN playwright install webkit
RUN apt-get update && apt-get install -y fonts-wqy-zenhei
RUN rm -rf /root/.cache/matplotlib/*
COPY app.py app.py
COPY firestore.py firestore.py
COPY gcs.py gcs.py
COPY gss.py gss.py
CMD ["python3", "app.py"]
EXPOSE 5000
#CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]