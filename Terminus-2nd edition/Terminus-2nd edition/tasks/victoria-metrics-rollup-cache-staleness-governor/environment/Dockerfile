FROM --platform=linux/amd64 public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac AS gobuild
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY cmd/ /app/cmd/
COPY internal/ /app/internal/
RUN go build -mod=readonly -o /out/vmrollup ./cmd/vmrollup

FROM --platform=linux/amd64 public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    build-essential gcc libc6-dev tmux asciinema \
    python3 python3-pip python3-venv sqlite3 ca-certificates \
 && rm -rf /var/lib/apt/lists/*
RUN python3 -m venv /opt/verifier-venv \
 && /opt/verifier-venv/bin/pip install --no-cache-dir \
    pytest==9.0.3 pytest-json-ctrf==0.5.0
COPY --from=gobuild /usr/local/go /usr/local/go
COPY --from=gobuild /go/pkg/mod /go/pkg/mod
COPY --from=gobuild /out/vmrollup /usr/local/bin/vmrollup
ENV PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
ENV GOCACHE=/opt/gocache
ENV GOFLAGS=-mod=readonly
WORKDIR /app
COPY go.mod go.sum ./
COPY cmd/ /app/cmd/
COPY internal/ /app/internal/
COPY docs/ /app/docs/
COPY fixtures/ /app/fixtures/
COPY config/ /app/config/
COPY data/ /app/data/
COPY scripts/ /app/scripts/
COPY README.md /app/README.md
RUN sed -i 's/\r$//' /app/scripts/*.sh \
 && chmod +x /app/scripts/reset-state.sh \
 && /app/scripts/reset-state.sh \
 && go build -mod=readonly -o /usr/local/bin/vmrollup ./cmd/vmrollup
COPY hidden-fixtures/ /opt/verifier-fixtures/
RUN mkdir -p /opt/tb3-probes \
 && cp /app/fixtures/scrapes/sample-counter.prom /opt/tb3-probes/sample-counter.prom
