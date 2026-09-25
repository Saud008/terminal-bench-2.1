FROM public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/opt/verifier-venv/bin:/usr/local/bin:/usr/bin:/bin:${PATH}"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    bash \
    ca-certificates \
    python3 \
    python3-pip \
    python3-venv \
    tmux \
    asciinema \
 && rm -rf /var/lib/apt/lists/* \
 && python3 -m venv /opt/verifier-venv \
 && /opt/verifier-venv/bin/pip install --no-cache-dir \
    pytest==9.0.3 \
    pytest-json-ctrf==0.5.0

WORKDIR /app
COPY bin/ /app/bin/
COPY lib/ /app/lib/
COPY docs/ /app/docs/
COPY fixtures/ /app/fixtures/
COPY scripts/ /app/scripts/
COPY config/ /app/config/
COPY README.md /app/README.md
COPY verifier-fixtures/ /opt/verifier-fixtures/

RUN mkdir -p /app/output /app/state \
 && sed -i 's/\r$//' /app/bin/pkctl /app/scripts/*.sh /app/lib/*.sh \
 && find /app/fixtures /app/docs -type f -exec sed -i 's/\r$//' {} + \
 && chmod +x /app/bin/pkctl /app/scripts/*.sh /app/lib/*.sh \
 && bash /app/scripts/reset-state.sh
