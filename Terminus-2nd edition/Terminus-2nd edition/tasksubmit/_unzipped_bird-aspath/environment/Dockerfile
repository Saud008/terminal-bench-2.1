FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac

LABEL org.opencontainers.image.title="bird-aspath-filter-peer-cutover-witness" \
      org.opencontainers.image.description="BGP AS-path export-filter peer cutover witness" \
      org.opencontainers.image.vendor="anonymous"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv tmux asciinema ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir \
       pytest==9.0.3 pytest-json-ctrf==0.5.0

COPY go.mod go.sum ./
COPY cmd ./cmd
COPY pwcore ./pwcore
COPY config ./config
COPY docs ./docs
COPY tools ./tools
COPY fixtures ./fixtures
COPY scripts ./scripts
COPY hidden/peers /opt/verifier-fixtures/bgpcut

RUN mkdir -p /app/state /app/output /app/bin \
    && find /app/scripts -name '*.sh' -exec sed -i 's/\r$//' {} + \
    && chmod +x /app/scripts/*.sh \
    && go build -o /usr/local/bin/bgpcut ./cmd/bgpcut

ENV PATH="/usr/local/go/bin:/usr/local/bin:/opt/verifier-venv/bin:${PATH}"
