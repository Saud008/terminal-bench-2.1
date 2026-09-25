FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac AS builder

WORKDIR /build
COPY go.mod go.sum ./
COPY cmd ./cmd
COPY internal ./internal
RUN go mod tidy && go build -o /build/migratectl ./cmd/migratectl

FROM public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates python3 python3-venv python3-pip tmux asciinema \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir \
    pytest==9.0.3 \
    pytest-json-ctrf==0.5.0

WORKDIR /app
COPY --from=builder /build/migratectl /app/bin/migratectl
COPY --from=builder /usr/local/go /usr/local/go
ENV PATH="/usr/local/go/bin:${PATH}"
COPY go.mod ./
COPY cmd ./cmd
COPY internal ./internal
COPY docs ./docs
COPY data ./data
RUN mkdir -p /app/state /app/output /app/bin
