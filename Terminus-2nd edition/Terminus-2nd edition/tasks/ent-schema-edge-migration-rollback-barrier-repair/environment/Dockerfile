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

COPY requirements.lock /tmp/requirements.lock
RUN python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir --require-hashes --no-deps -r /tmp/requirements.lock \
    && rm -f /tmp/requirements.lock

ENV PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
ENV CGO_ENABLED=0

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY cmd/ /app/cmd/
COPY internal/ /app/internal/
COPY docs/ /app/docs/
COPY fixtures/ /app/fixtures/
COPY verifier-fixtures/ /opt/verifier-fixtures/ent-edge/
COPY scripts/ /app/scripts/
COPY README.md /app/README.md

RUN sed -i 's/\r$//' /app/scripts/*.sh \
    && chmod +x /app/scripts/reset-state.sh /app/scripts/verifier-rebuild.sh \
    && mkdir -p /app/output /app/work \
    && go build -mod=readonly -trimpath -ldflags="-s -w" -o /usr/local/bin/entmigrate ./cmd/entmigrate
