FROM --platform=linux/amd64 public.ecr.aws/docker/library/python:3.13-slim-bookworm@sha256:01f42367a0a94ad4bc17111776fd66e3500c1d87c15bbd6055b7371d39c124fb

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
 && rm -rf /var/lib/apt/lists/* \
 && command -v tmux >/dev/null \
 && command -v asciinema >/dev/null

COPY requirements.txt /tmp/requirements.txt
RUN python3 -m venv /opt/verifier-venv \
 && /opt/verifier-venv/bin/pip install --no-cache-dir --require-hashes -r /tmp/requirements.txt \
 && rm -f /tmp/requirements.txt

WORKDIR /app

COPY bin/ /app/bin/
COPY lib/ /app/lib/
COPY docs/ /app/docs/
COPY fixtures/ /app/fixtures/
COPY scripts/ /app/scripts/
COPY README.md /app/README.md

RUN sed -i 's/\r$//' /app/bin/tmpfiles-replay /app/scripts/*.sh /app/lib/*.sh \
 && chmod +x /app/bin/tmpfiles-replay /app/scripts/*.sh /app/lib/*.sh \
 && mkdir -p /app/output /app/work/tree /opt/verifier-broken-tmpfiles \
 && cp /app/lib/age_eval.sh /opt/verifier-broken-tmpfiles/age_eval.sh \
 && cp /app/lib/glob_prune.sh /opt/verifier-broken-tmpfiles/glob_prune.sh \
 && cp /app/lib/recreate_seq.sh /opt/verifier-broken-tmpfiles/recreate_seq.sh \
 && cp /app/lib/ownership.sh /opt/verifier-broken-tmpfiles/ownership.sh \
 && cp /app/lib/generator_merge.sh /opt/verifier-broken-tmpfiles/generator_merge.sh \
 && bash /app/scripts/reset-state.sh
