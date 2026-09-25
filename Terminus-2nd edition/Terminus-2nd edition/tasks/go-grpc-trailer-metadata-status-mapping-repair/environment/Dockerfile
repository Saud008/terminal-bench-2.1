FROM --platform=linux/amd64 public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    asciinema \
    ca-certificates \
    python3 \
    python3-pip \
    python3-venv \
    tmux \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN python3 -m venv /opt/verifier-venv \
 && /opt/verifier-venv/bin/pip install --no-cache-dir --require-hashes -r /tmp/requirements.txt \
 && rm -f /tmp/requirements.txt

ENV PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/go/bin:/usr/local/bin:${PATH}"
ENV GOCACHE=/opt/gocache
ENV GOFLAGS=-mod=readonly

RUN mkdir -p /opt/gocache \
 && go install google.golang.org/protobuf/cmd/protoc-gen-go@v1.35.1 \
 && go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@v1.5.1 \
 && go install github.com/fullstorydev/grpcurl/cmd/grpcurl@v1.9.2 \
 && cp /go/bin/grpcurl /usr/local/bin/grpcurl

WORKDIR /app

COPY go.mod go.sum ./
COPY proto/ proto/
COPY api/ api/
COPY scripts/gen-proto.sh scripts/

COPY cmd/ cmd/
COPY internal/ internal/
COPY docs/ docs/
COPY fixtures/ fixtures/
COPY verifier-fixtures/grpc/ /opt/verifier-fixtures/grpc/
COPY scripts/ scripts/
COPY README.md ./

RUN go build -mod=readonly -o /usr/local/bin/grpcfaultd ./cmd/grpcfaultd \
 && go build -mod=readonly -o /usr/local/bin/frameprobe ./cmd/frameprobe \
 && chmod +x /app/scripts/*.sh \
 && mkdir -p /app/output \
 && bash /app/scripts/reset-state.sh
