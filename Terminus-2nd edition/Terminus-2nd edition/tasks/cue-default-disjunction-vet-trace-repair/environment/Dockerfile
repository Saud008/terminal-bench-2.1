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

COPY requirements.txt /tmp/requirements.txt
RUN python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir --require-hashes -r /tmp/requirements.txt \
    && rm -f /tmp/requirements.txt

ENV PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY cmd/ cmd/
COPY internal/ internal/
COPY docs/ docs/
COPY workspaces/ workspaces/
COPY fixtures/ fixtures/
COPY fixtures/hidden/ /opt/verifier-fixtures/workspaces/
COPY scripts/ scripts/
COPY README.md README.md

RUN sed -i 's/\r$//' /app/scripts/*.sh \
    && chmod +x /app/scripts/*.sh \
    && mkdir -p /app/output \
    && go build -o /usr/local/bin/cuectl ./cmd/cuectl \
    && mkdir -p /opt/verifier-broken-cuewrap \
    && cp /app/internal/cuewrap/disjunct.go /opt/verifier-broken-cuewrap/disjunct.go \
    && cp /app/internal/cuewrap/closed.go /opt/verifier-broken-cuewrap/closed.go \
    && cp /app/internal/cuewrap/embed.go /opt/verifier-broken-cuewrap/embed.go \
    && cp /app/internal/cuewrap/compose.go /opt/verifier-broken-cuewrap/compose.go \
    && cp /app/internal/cuewrap/snapshot_bind.go /opt/verifier-broken-cuewrap/snapshot_bind.go \
    && cp /app/internal/cuewrap/snapshot_guard.go /opt/verifier-broken-cuewrap/snapshot_guard.go \
    && cp /app/internal/cuewrap/diag_linefmt.go /opt/verifier-broken-cuewrap/diag_linefmt.go \
    && cp /app/internal/cuewrap/vet.go /opt/verifier-broken-cuewrap/vet.go \
    && cp /app/internal/cuewrap/export.go /opt/verifier-broken-cuewrap/export.go \
    && bash /app/scripts/reset-state.sh
