FROM --platform=linux/amd64 public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac

ENV CGO_ENABLED=1
ENV GOFLAGS=-mod=readonly
ENV PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
ENV GOCACHE=/opt/gocache

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        libc6-dev \
        tmux \
        asciinema \
        python3 \
        python3-pip \
        python3-venv \
        sqlite3 \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir --require-hashes -r /tmp/requirements.txt \
    && rm -f /tmp/requirements.txt

RUN mkdir -p /opt/gocache

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY cmd/ /app/cmd/
COPY internal/ /app/internal/
COPY docs/ /app/docs/
COPY fixtures/ /app/fixtures/
COPY data/ /app/data/
COPY scripts/ /app/scripts/
COPY README.md /app/README.md
COPY opt-fixtures/ /opt/verifier-fixtures/

RUN chmod +x /app/scripts/reset-state.sh \
    && sqlite3 /app/data/thread.db < /app/data/schema.sql \
    && cp /app/data/thread.db /app/data/thread.db.bak \
    && mkdir -p /app/output /app/state \
    && go build -mod=readonly -o /usr/local/bin/mailindex ./cmd/mailindex
