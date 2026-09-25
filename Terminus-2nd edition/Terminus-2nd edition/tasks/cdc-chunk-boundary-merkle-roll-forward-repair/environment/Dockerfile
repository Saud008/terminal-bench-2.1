FROM --platform=linux/amd64 public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac AS gobuild

WORKDIR /build
COPY go.mod go.sum ./
RUN go mod download

COPY cmd/ ./cmd/
COPY internal/ ./internal/

ENV CGO_ENABLED=0
ENV GOFLAGS=-mod=readonly
ENV GOCACHE=/tmp/gocache

RUN mkdir -p /tmp/gocache \
    && go build -mod=readonly -trimpath -ldflags="-s -w" -o /cdcctl ./cmd/cdcctl

FROM --platform=linux/amd64 public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema \
        bash \
        ca-certificates \
        python3 \
        python3-pip \
        python3-venv \
        tmux \
    && rm -rf /var/lib/apt/lists/*

COPY --from=gobuild /usr/local/go /usr/local/go
COPY --from=gobuild /cdcctl /usr/local/bin/cdcctl
COPY --from=gobuild /tmp/gocache /opt/gocache
COPY requirements.txt /tmp/requirements.txt

RUN python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir --require-hashes -r /tmp/requirements.txt \
    && rm -f /tmp/requirements.txt

ENV PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
ENV GOCACHE=/opt/gocache
ENV GOFLAGS=-mod=readonly
ENV CGO_ENABLED=0

RUN printf '%s\n' 'export PATH="/usr/local/go/bin:${PATH}"' > /etc/profile.d/go-path.sh

WORKDIR /app
COPY go.mod go.sum ./
COPY cmd/ /app/cmd/
COPY internal/ /app/internal/
COPY docs/ /app/docs/
COPY config/ /app/config/
COPY scripts/ /app/scripts/
COPY tools/ /app/tools/
COPY README.md /app/README.md

RUN sed -i 's/\r$//' /app/scripts/*.sh \
    && chmod +x /app/scripts/*.sh \
    && python3 /app/tools/gen_fixtures.py \
    && mkdir -p /app/output /app/state \
    && bash /app/scripts/reset-state.sh
