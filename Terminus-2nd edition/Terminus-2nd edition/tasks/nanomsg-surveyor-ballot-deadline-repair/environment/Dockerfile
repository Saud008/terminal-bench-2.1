FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac

COPY requirements.txt /tmp/requirements.txt
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tmux \
        asciinema \
        python3 \
        python3-venv \
        ca-certificates \
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
COPY docs/ docs/
COPY fixtures/ fixtures/
COPY scripts/ scripts/
COPY README.md ./

COPY verifier-fixtures/ /opt/verifier-fixtures/

RUN find /app/scripts -name '*.sh' -exec sed -i 's/\r$//' {} + \
    && find /opt/verifier-fixtures -type f -name '*.json' -exec sed -i 's/\r$//' {} + \
    && chmod +x /app/scripts/*.sh \
    && mkdir -p /app/output /app/state /opt/verifier-broken-ballotmesh \
    && cp /app/internal/surveyor/fsm.go /opt/verifier-broken-ballotmesh/fsm.go \
    && cp /app/internal/ballot/merge.go /opt/verifier-broken-ballotmesh/merge.go \
    && cp /app/internal/ttl/session.go /opt/verifier-broken-ballotmesh/session.go \
    && cp /app/internal/frame/header.go /opt/verifier-broken-ballotmesh/header.go \
    && cp /app/internal/topology/dedup.go /opt/verifier-broken-ballotmesh/dedup.go \
    && cp /app/internal/export/publish.go /opt/verifier-broken-ballotmesh/publish.go \
    && cp /app/internal/export/stats.go /opt/verifier-broken-ballotmesh/stats.go \
    && cp /app/internal/staging/snapshot.go /opt/verifier-broken-ballotmesh/snapshot.go \
    && cp /app/internal/ingest/mesh.go /opt/verifier-broken-ballotmesh/mesh.go \
    && cp /app/internal/simulate/engine.go /opt/verifier-broken-ballotmesh/engine.go \
    && go build -mod=readonly -o /usr/local/bin/ballotmesh ./cmd/ballotmesh \
    && /app/scripts/reset-state.sh
