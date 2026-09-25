FROM --platform=linux/amd64 public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac AS verifier-deps

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN python3 -m venv /opt/verifier-venv \
 && /opt/verifier-venv/bin/pip install --no-cache-dir -r /tmp/requirements.txt \
 && rm -f /tmp/requirements.txt

FROM --platform=linux/amd64 public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    asciinema \
    ca-certificates \
    curl \
    python3 \
    tmux \
 && rm -rf /var/lib/apt/lists/*

COPY --from=verifier-deps /opt/verifier-venv /opt/verifier-venv

ENV PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
ENV GOCACHE=/opt/gocache
ENV GOFLAGS=-mod=readonly
ENV PYTHONDONTWRITEBYTECODE=1

RUN mkdir -p /opt/gocache /logs/verifier

WORKDIR /app
COPY go.mod ./
COPY cmd/ cmd/
COPY internal/ internal/
COPY docs/ docs/
COPY fixtures/ fixtures/
COPY scripts/ scripts/
COPY README.md ./

RUN find /app/fixtures /app/scripts -type f \( -name '*.json' -o -name '*.sh' \) -exec sed -i 's/\x0d$//' {} + \
 && chmod +x /app/scripts/*.sh \
 && go mod tidy \
 && go build -mod=readonly -o /usr/local/bin/variantgate ./cmd/variantgate \
 && mkdir -p /opt/verifier-broken-gate /app/output /app/state \
 && cp /app/internal/negotiate/prepare.go /opt/verifier-broken-gate/prepare.go \
 && cp /app/internal/negotiate/select.go /opt/verifier-broken-gate/select.go \
 && cp /app/internal/negotiate/rank.go /opt/verifier-broken-gate/rank.go \
 && cp /app/internal/negotiate/language.go /opt/verifier-broken-gate/language.go \
 && cp /app/internal/cache/response.go /opt/verifier-broken-gate/response.go \
 && cp /app/internal/staging/snapshot.go /opt/verifier-broken-gate/snapshot.go \
 && cp /app/internal/staging/publish.go /opt/verifier-broken-gate/publish.go \
 && cp /app/internal/staging/guard.go /opt/verifier-broken-gate/guard.go \
 && /app/scripts/reset-state.sh
