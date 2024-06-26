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

ENV EPA_TOKEN ${EPA_TOKEN}
ENV CWA_TOKEN ${CWA_TOKEN}
ENV ACCESS_TOKEN ${ACCESS_TOKEN}
ENV SECRET ${SECRET}
ENV OPENAI_TOKEN ${OPENAI_TOKEN}
ENV GOOGLE_APPLICATION_CREDENTIALS ${GOOGLE_APPLICATION_CREDENTIALS}
ENV LOG_PATH ${LOG_PATH}
ENV GMAP_API_KEY ${GMAP_API_KEY}

RUN pip3 install -r requirements.txt &&\
    playwright install firefox --with-deps &&\
    apt-get update && apt-get install -y fonts-wqy-zenhei ffmpeg &&\
    rm -rf /root/.cache/matplotlib/* &&\
    mkdir /app/videos &&\
    mkdir -p /var/log/line-bot
COPY app.py app.py
COPY firestore.py firestore.py
COPY gcs.py gcs.py
COPY gss.py gss.py
COPY lma.py lma.py
CMD ["python3", "app.py"]
EXPOSE 5000
#CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]