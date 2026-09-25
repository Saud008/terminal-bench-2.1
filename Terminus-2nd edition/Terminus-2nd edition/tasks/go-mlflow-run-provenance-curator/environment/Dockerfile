FROM --platform=linux/amd64 public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac AS builder

WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download

COPY cmd/ /src/cmd/
COPY internal/ /src/internal/
COPY config/ /src/config/
COPY docs/ /src/docs/
COPY fixtures/ /src/fixtures/
COPY scripts/ /src/scripts/

RUN sed -i 's/\r$//' /src/scripts/*.sh \
    && go build -mod=readonly -trimpath -ldflags="-s -w" -o /tmp/mlprov ./cmd/mlprov

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
COPY config/ /app/config/
COPY docs/ /app/docs/
COPY fixtures/ /app/fixtures/
COPY scripts/ /app/scripts/
COPY --from=builder /tmp/mlprov /usr/local/bin/mlprov

RUN sed -i 's/\r$//' /app/scripts/*.sh \
    && chmod +x /app/scripts/reset-state.sh /app/scripts/verifier-rebuild.sh \
    && mkdir -p /app/work /app/state /app/output
