FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        patch \
        tmux \
        asciinema \
        python3 \
        python3-venv \
        python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir pytest==8.4.1 pytest-json-ctrf==0.3.5

ENV PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
ENV CGO_ENABLED=0

WORKDIR /app
COPY go.mod go.sum ./
COPY cmd ./cmd
COPY internal ./internal
COPY docs ./docs
COPY fixtures ./fixtures
COPY scripts ./scripts
COPY hidden /opt/verifier-fixtures/vaultaud_renewal_hidden

RUN sed -i 's/\r$//' /app/scripts/*.sh \
    && find /app/internal /app/cmd -name '*.go' -exec sed -i 's/\r$//' {} + \
    && chmod +x /app/scripts/rebuild-vaultaud.sh /app/scripts/reset-state.sh \
    && python3 /app/fixtures/build_fixtures.py \
    && mkdir -p /app/state /app/output /app/bin \
    && go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/vaultaud ./cmd/vaultaud
