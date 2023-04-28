FROM python:3.9.16-slim
RUN mkdir -p /var/log/line-bot
WORKDIR /app
COPY requirements.txt requirements.txt

ARG EPA_TOKEN
ARG CWB_TOKEN
ARG ACCESS_TOKEN
ARG SECRET
ARG OPENAI_TOKEN

ENV EPA_TOKEN ${EPA_TOKEN}
ENV CWB_TOKEN ${CWB_TOKEN}
ENV ACCESS_TOKEN ${ACCESS_TOKEN}
ENV SECRET ${SECRET}
ENV OPENAI_TOKEN ${OPENAI_TOKEN}

RUN pip3 install -r requirements.txt
COPY app.py app.py
COPY firestore.py firestore.py
CMD ["python3", "app.py"]
#CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]