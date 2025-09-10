FROM python:3.13

RUN apt-get update && \
    apt-get install -y swi-prolog

# SWI_HOME_DIR=/usr/lib/swi-prolog
# LIBSWIPL_PATH=/lib/aarch64-linux-gnu/libswipl.so.9

ENV SWI_HOME_DIR=/usr/lib/swi-prolog
ENV LIBSWIPL_PATH=/lib/aarch64-linux-gnu/libswipl.so.9

# CREATE /app
WORKDIR /app

# COPY main.py only
COPY ./main.py /app/main.py
COPY ./agent.pl /app/agent.pl
COPY ./pyproject.toml /app/pyproject.toml

RUN pip3 install --no-cache-dir .