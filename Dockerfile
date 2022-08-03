FROM python:3.7

ARG IMAGE_TAG_ARG='m-default'
ARG TOKEN_NAME='test'
ARG TOKEN_KEY=''

ENV IMAGE_TAG=${IMAGE_TAG_ARG}
ENV TOKEN_NAME=${TOKEN_NAME}
ENV TOKEN_KEY=${TOKEN_KEY}

WORKDIR /app

ARG SSH_PRIVATE_KEY
RUN mkdir -p /root/.ssh/ && \
    chmod 700 /root/.ssh && \
    echo "$SSH_PRIVATE_KEY" > /root/.ssh/id_ed25519 && \
    chmod 600 /root/.ssh/id_ed25519 && \
    touch /root/.ssh/known_hosts && \
    ssh-keyscan git.teko.vn >> /root/.ssh/known_hosts

ADD requirements.txt /app/

RUN pip install -r requirements.txt

RUN if [ ! -d "media" ]; then mkdir media; fi

ADD . /app

RUN ln -s /app/docs /app/media/

ENV prometheus_multiproc_dir /tmp

CMD ["gunicorn", "main:app", "-k", "gevent", "--bind=0.0.0.0:8000", "--workers=2"]
