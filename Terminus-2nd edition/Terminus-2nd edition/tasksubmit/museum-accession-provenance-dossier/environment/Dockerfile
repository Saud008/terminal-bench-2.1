FROM --platform=linux/amd64 public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        ca-certificates \
        python3 \
        python3-pip \
        python3-venv \
        tmux \
        asciinema \
        sqlite3 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.lock /tmp/requirements.lock
RUN python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir --require-hashes -r /tmp/requirements.lock \
    && rm -f /tmp/requirements.lock

ENV PATH="/opt/verifier-venv/bin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH}"
ENV PYTHONPATH="/app/lib:${PYTHONPATH}"

WORKDIR /app

COPY lib/ /app/lib/
COPY config/ /app/config/
COPY docs/ /app/docs/
COPY fixtures/ /app/fixtures/
COPY scripts/ /app/scripts/

RUN mkdir -p /app/state /app/work /app/output /logs/verifier \
    && find /app/scripts /app/lib -type f \( -name '*.sh' -o -name 'musdoss' -o -name '*.py' \) -exec sed -i 's/\r$//' {} + \
    && chmod +x /app/scripts/*.sh /app/scripts/musdoss \
    && install -m 0755 /app/scripts/musdoss /usr/local/bin/musdoss \
    && bash /app/scripts/reset-state.sh
