FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        python3 \
        python3-venv \
    && apt-get purge -y make \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/pytools \
    && /opt/pytools/bin/pip install --no-cache-dir pytest==8.4.1 pytest-json-ctrf==0.3.5

ENV GOTOOLCHAIN=local \
    CGO_ENABLED=0

COPY . /tests/

RUN mkdir -p /app

WORKDIR /app
