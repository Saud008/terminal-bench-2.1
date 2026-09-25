FROM --platform=linux/amd64 public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        python3=3.11.2-1+b1 \
        python3-venv=3.11.2-1+b1 \
        python3-pip=23.0.1+dfsg-1 \
    && rm -rf /var/lib/apt/lists/* \
    && python3 -m venv /opt/verifier-venv

COPY requirements.lock /tmp/requirements.lock
RUN /opt/verifier-venv/bin/pip install --no-cache-dir --require-hashes --no-deps -r /tmp/requirements.lock \
    && rm -f /tmp/requirements.lock

COPY . /tests/
RUN chmod +x /tests/test.sh && mkdir -p /logs/verifier
