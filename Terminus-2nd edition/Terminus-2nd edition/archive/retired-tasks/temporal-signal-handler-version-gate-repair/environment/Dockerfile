FROM --platform=linux/amd64 public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tmux \
        asciinema \
        python3 \
        python3-pip \
        python3-venv \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir \
        pytest==9.0.3 \
        pytest-json-ctrf==0.5.0

ENV PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
ENV GOCACHE=/opt/gocache
ENV GOFLAGS=-mod=readonly

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY cmd/ cmd/
COPY internal/ internal/
COPY docs/ docs/
COPY config/ config/
COPY fixtures/ fixtures/
COPY scripts/ scripts/
COPY README.md ./
COPY verifier-fixtures/ /opt/verifier-fixtures/

RUN sed -i 's/\r$//' /app/scripts/*.sh \
    && chmod +x /app/scripts/reset-state.sh /app/scripts/build-cli.sh /app/scripts/verifier-rebuild.sh \
    && mkdir -p /app/output /app/state /opt/verifier-broken-temporal \
    && cp /app/internal/router/dispatch.go /opt/verifier-broken-temporal/dispatch.go \
    && cp /app/internal/version/gate.go /opt/verifier-broken-temporal/gate.go \
    && cp /app/internal/handler/ack.go /opt/verifier-broken-temporal/ack.go \
    && cp /app/internal/dedup/ledger.go /opt/verifier-broken-temporal/dedup.go \
    && cp /app/internal/heartbeat/clock.go /opt/verifier-broken-temporal/clock.go \
    && cp /app/internal/export/history.go /opt/verifier-broken-temporal/export.go \
    && cp /app/internal/staging/snapshot.go /opt/verifier-broken-temporal/staging.go \
    && cp -a /app/internal /opt/verifier-broken-temporal-src \
    && go build -mod=readonly -o /usr/local/bin/temporal-signal-replay ./cmd/temporal-signal-replay \
    && bash /app/scripts/reset-state.sh
