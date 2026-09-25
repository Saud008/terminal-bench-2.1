FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac AS builder

WORKDIR /build
COPY go.mod go.sum ./
RUN go mod download
COPY cmd/ ./cmd/
COPY internal/ ./internal/
COPY merge/ ./merge/
COPY pkg/ ./pkg/
RUN CGO_ENABLED=0 go build -mod=readonly -o /build/shadow-sync ./cmd/shadow-sync

FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        tmux \
        asciinema \
        python3 \
        python3-pip \
        python3-venv \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir \
        pytest==8.4.1 \
        pytest-json-ctrf==0.3.5

ENV PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/app/bin:${PATH}"
ENV CGO_ENABLED=0
ENV GOCACHE=/opt/gocache
ENV GOFLAGS=-mod=readonly

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY cmd/ /app/cmd/
COPY internal/ /app/internal/
COPY merge/ /app/merge/
COPY pkg/ /app/pkg/
COPY docs/ /app/docs/
COPY fixtures/ /app/fixtures/
COPY fixtures-tb3/ /opt/verifier-fixtures/
COPY Makefile README.md /app/
COPY --from=builder /build/shadow-sync /app/bin/shadow-sync

RUN mkdir -p /app/state /app/output /opt/gocache /app/bin \
    && go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/shadow-sync ./cmd/shadow-sync
