FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac

COPY requirements.txt /tmp/requirements.txt
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tmux \
        asciinema \
        python3 \
        python3-venv \
        ca-certificates \
        sqlite3 \
    && rm -rf /var/lib/apt/lists/* \
    && python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir --require-hashes -r /tmp/requirements.txt \
    && rm -f /tmp/requirements.txt

ENV PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
ENV GOFLAGS=-mod=readonly

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY cmd/ cmd/
COPY internal/ internal/
COPY config/ config/
COPY docs/ docs/
COPY fixtures/ fixtures/
COPY scripts/ scripts/
COPY README.md ./

RUN find /app/scripts -name '*.sh' -exec sed -i 's/\r$//' {} + \
    && chmod +x /app/scripts/*.sh \
    && mkdir -p /app/output /app/state /app/data /logs/verifier /opt/verifier-broken-chparts/ingest /opt/verifier-broken-chparts/merge /opt/verifier-broken-chparts/commit /opt/verifier-broken-chparts/ttl /opt/verifier-broken-chparts/export /opt/verifier-broken-chparts/staging \
    && cp /app/internal/ingest/register.go /opt/verifier-broken-chparts/ingest/register.go \
    && cp /app/internal/ingest/idempotency.go /opt/verifier-broken-chparts/ingest/idempotency.go \
    && cp /app/internal/merge/comparator.go /opt/verifier-broken-chparts/merge/comparator.go \
    && cp /app/internal/commit/barrier.go /opt/verifier-broken-chparts/commit/barrier.go \
    && cp /app/internal/ttl/drop.go /opt/verifier-broken-chparts/ttl/drop.go \
    && cp /app/internal/export/publish.go /opt/verifier-broken-chparts/export/publish.go \
    && cp /app/internal/staging/snapshot.go /opt/verifier-broken-chparts/staging/snapshot.go \
    && go build -mod=readonly -o /usr/local/bin/chparts ./cmd/chparts \
    && /app/scripts/reset-state.sh
