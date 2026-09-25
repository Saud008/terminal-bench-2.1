FROM public.ecr.aws/docker/library/python:3.13-slim-bookworm@sha256:01f42367a0a94ad4bc17111776fd66e3500c1d87c15bbd6055b7371d39c124fb

ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV TZ=UTC

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    bash \
    ca-certificates \
    coreutils \
    tmux \
    asciinema \
    tzdata \
 && rm -rf /var/lib/apt/lists/* \
 && command -v tmux >/dev/null \
 && command -v asciinema >/dev/null

COPY requirements.txt /tmp/requirements.txt
RUN python3 -m venv /opt/verifier-venv \
 && /opt/verifier-venv/bin/pip install --no-cache-dir --require-hashes -r /tmp/requirements.txt \
 && rm -f /tmp/requirements.txt

WORKDIR /app

COPY scripts/ /app/scripts/
COPY lib/ /app/lib/
COPY docs/ /app/docs/
COPY fixtures/ /app/fixtures/
COPY README.md /app/README.md

RUN mkdir -p /app/bin \
 && install -m 0755 /app/scripts/at-replay /app/bin/at-replay \
 && sed -i 's/\r$//' /app/bin/at-replay /app/scripts/*.sh /app/lib/*.sh \
 && chmod +x /app/scripts/*.sh /app/lib/*.sh \
 && mkdir -p /app/output /app/work/scripts /app/work/registry /app/var/spool/at/jobs /app/var/spool/at/batch_slots /opt/verifier-broken-atd \
 && cp /app/lib/spool.sh /opt/verifier-broken-atd/spool.sh \
 && cp /app/lib/slots.sh /opt/verifier-broken-atd/slots.sh \
 && cp /app/lib/mail.sh /opt/verifier-broken-atd/mail.sh \
 && cp /app/lib/atq.sh /opt/verifier-broken-atd/atq.sh \
 && cp /app/lib/seq.sh /opt/verifier-broken-atd/seq.sh \
 && bash /app/scripts/reset-state.sh
