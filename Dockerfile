FROM python:3.9.16-slim
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
COPY . .
CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]