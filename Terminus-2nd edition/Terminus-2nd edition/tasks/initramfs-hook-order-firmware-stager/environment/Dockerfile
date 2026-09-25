FROM public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        python3 \
        python3-pip \
        python3-venv \
        tmux \
        asciinema \
        ca-certificates \
        coreutils \
        findutils \
    && rm -rf /var/lib/apt/lists/* \
    && command -v tmux >/dev/null \
    && command -v asciinema >/dev/null

COPY requirements.txt /tmp/verifier-requirements.txt
RUN python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir --require-hashes -r /tmp/verifier-requirements.txt \
    && rm -f /tmp/verifier-requirements.txt

ENV PATH="/opt/verifier-venv/bin:/usr/local/bin:/usr/bin:/bin"

WORKDIR /app

COPY bin/ /app/bin/
COPY lib/ /app/lib/
COPY docs/ /app/docs/
COPY fixtures/ /app/fixtures/
COPY config/ /app/config/
COPY scripts/ /app/scripts/
COPY README.md /app/README.md
COPY opt-verifier-fixtures/ /opt/verifier-fixtures/

RUN sed -i 's/\r$//' /app/bin/irfs-stage /app/scripts/*.sh /app/lib/*/*.sh /app/lib/*/*/*.sh 2>/dev/null || true \
    && find /app/lib -name '*.sh' -exec chmod +x {} + \
    && chmod +x /app/bin/irfs-stage /app/scripts/*.sh \
    && install -m 0755 /app/bin/irfs-stage /usr/local/bin/irfs-stage \
    && mkdir -p /app/output /app/state \
    && bash /app/scripts/reset-state.sh
