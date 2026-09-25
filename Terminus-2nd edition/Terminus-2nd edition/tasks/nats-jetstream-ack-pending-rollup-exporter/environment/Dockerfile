FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac AS builder

WORKDIR /build
COPY go.mod ./
COPY cmd ./cmd
COPY internal ./internal
RUN go build -o /build/natsctl ./cmd/natsctl

FROM public.ecr.aws/docker/library/python:3.13-slim-bookworm@sha256:01f42367a0a94ad4bc17111776fd66e3500c1d87c15bbd6055b7371d39c124fb

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --no-cache-dir \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

WORKDIR /app
COPY --from=builder /build/natsctl /app/bin/natsctl
COPY go.mod ./
COPY cmd ./cmd
COPY internal ./internal
COPY docs ./docs
COPY data ./data
RUN mkdir -p /app/state /app/output /app/bin
