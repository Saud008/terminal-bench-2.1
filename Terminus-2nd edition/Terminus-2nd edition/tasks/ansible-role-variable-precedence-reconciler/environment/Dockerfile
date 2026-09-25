FROM --platform=linux/amd64 public.ecr.aws/docker/library/python:3.13-slim-bookworm@sha256:01f42367a0a94ad4bc17111776fd66e3500c1d87c15bbd6055b7371d39c124fb

ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/opt/verifier-venv/bin:/usr/local/bin:/usr/bin:/bin:${PATH}"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    bash \
    ca-certificates \
    coreutils \
    tmux \
    asciinema \
 && rm -rf /var/lib/apt/lists/* \
 && python3 -m venv /opt/verifier-venv

COPY requirements.lock /tmp/requirements.lock
RUN /opt/verifier-venv/bin/pip install --no-cache-dir --require-hashes -r /tmp/requirements.lock

WORKDIR /app

COPY bin/ /app/bin/
COPY lib/ /app/lib/
COPY tools/ /app/tools/
COPY scripts/ /app/scripts/
COPY docs/ /app/docs/
COPY inventory/ /app/inventory/
COPY roles/ /app/roles/
COPY playbooks/ /app/playbooks/
COPY vars/ /app/vars/
COPY fixtures-tb3/ /opt/verifier-fixtures/
COPY README.md /app/README.md

RUN sed -i 's/\r$//' /app/bin/ansible-var-merge /app/scripts/*.sh /app/lib/*.sh /app/lib/decoy/*.sh /app/lib/staging/*.sh \
 && chmod +x /app/bin/ansible-var-merge /app/scripts/*.sh /app/lib/*.sh /app/lib/decoy/*.sh /app/lib/staging/*.sh \
 && chmod +x /app/tools/var_loader.py \
 && mkdir -p /app/output \
 && : > /app/output/.resolve-touch
