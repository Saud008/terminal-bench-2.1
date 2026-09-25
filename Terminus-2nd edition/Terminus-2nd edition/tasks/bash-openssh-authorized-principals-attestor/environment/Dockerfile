FROM --platform=linux/amd64 public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    bash \
    coreutils \
    gawk \
    jq \
    patch \
    ca-certificates \
    python3 \
    python3-venv \
    tmux \
    asciinema \
 && rm -rf /var/lib/apt/lists/* \
 && command -v tmux >/dev/null \
 && command -v asciinema >/dev/null

COPY requirements.txt /tmp/requirements.txt
RUN python3 -m venv /opt/verifier-venv \
 && /opt/verifier-venv/bin/pip install --no-cache-dir --require-hashes -r /tmp/requirements.txt \
 && rm -f /tmp/requirements.txt

ENV PATH="/opt/verifier-venv/bin:/usr/local/bin:/usr/bin:/bin:${PATH}"

WORKDIR /app

COPY lib/ /app/lib/
COPY Makefile /app/Makefile
COPY config/ /app/config/
COPY docs/ /app/docs/
COPY fixtures/ /app/fixtures/
COPY scripts/ /app/scripts/
COPY opt-verifier-fixtures/ /opt/verifier-fixtures/
COPY README.md /app/README.md

RUN mkdir -p /app/state /app/output \
 && find /app -name '*.sh' -o -name 'sshap' | while read -r f; do sed -i 's/\r$//' "$f"; done \
 && chmod +x /app/scripts/sshap /app/scripts/*.sh \
 && find /app/lib -name '*.sh' -exec chmod +x {} + \
 && install -m 0755 /app/scripts/sshap /usr/local/bin/sshap \
 && bash /app/scripts/reset-state.sh

LABEL org.opencontainers.image.source="terminus/tasks/bash-openssh-authorized-principals-attestor"
