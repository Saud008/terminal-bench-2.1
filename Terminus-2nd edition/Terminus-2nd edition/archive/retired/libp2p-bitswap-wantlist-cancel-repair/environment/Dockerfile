FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tmux \
        asciinema \
        python3 \
        python3-pip \
        python3-venv \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir \
        pytest==9.0.3 \
        pytest-json-ctrf==0.5.0

ENV PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
ENV GOCACHE=/opt/gocache
ENV GOFLAGS=-mod=readonly

RUN mkdir -p /opt/gocache /opt/verifier-fixtures/bitswap /app/state /app/output

WORKDIR /app
COPY go.mod ./
RUN go mod download

COPY cmd/ /app/cmd/
COPY internal/ /app/internal/
COPY docs/ /app/docs/
COPY fixtures/ /app/fixtures/
COPY scripts/ /app/scripts/
COPY README.md /app/README.md

RUN printf '%s\n' \
    '{"seq":1,"op":"want","cid":"bafyAA0000000000000000000000000000000000000000000000000000000000000001","priority":6}' \
    '{"seq":2,"op":"merge_wants","wants":[{"cid":"QmAlias000000000000000000000000000000000000000000000000000000000001","priority":11}]}' \
    '{"seq":3,"op":"block_done","cid":"bafyAA0000000000000000000000000000000000000000000000000000000000000001","peer":"hidden-a","bytes":400}' \
    > /opt/verifier-fixtures/bitswap/hidden-alias-dedupe.jsonl \
    && printf '%s\n' \
    '{"seq":1,"op":"want","cid":"bafyAA0000000000000000000000000000000000000000000000000000000000000003","priority":7}' \
    '{"seq":2,"op":"block_start","cid":"bafyAA0000000000000000000000000000000000000000000000000000000000000003","peer":"hidden-b","bytes":90}' \
    '{"seq":3,"op":"cancel","cid":"bafyAA0000000000000000000000000000000000000000000000000000000000000003"}' \
    '{"seq":4,"op":"block_done","cid":"bafyAA0000000000000000000000000000000000000000000000000000000000000003","peer":"hidden-b","bytes":90}' \
    > /opt/verifier-fixtures/bitswap/hidden-cancel-inflight.jsonl \
    && printf '%s\n' \
    '{"seq":1,"op":"want","cid":"bafyAA0000000000000000000000000000000000000000000000000000000000000002","priority":2}' \
    '{"seq":2,"op":"block_start","cid":"bafyAA0000000000000000000000000000000000000000000000000000000000000002","peer":"hidden-c","bytes":50}' \
    '{"seq":3,"op":"block_done","cid":"bafyAA0000000000000000000000000000000000000000000000000000000000000002","peer":"hidden-c","bytes":50}' \
    '{"seq":4,"op":"block_done","cid":"bafyAA0000000000000000000000000000000000000000000000000000000000000002","peer":"hidden-c","bytes":50}' \
    > /opt/verifier-fixtures/bitswap/hidden-ledger-once.jsonl \
    && printf '%s\n' \
    '{"seq":1,"op":"want","cid":"bafyAA0000000000000000000000000000000000000000000000000000000000000004","priority":4}' \
    '{"seq":2,"op":"block_part","cid":"bafyAA0000000000000000000000000000000000000000000000000000000000000004","peer":"hidden-d","bytes":180}' \
    '{"seq":3,"op":"tick","idle_ms":5000}' \
    > /opt/verifier-fixtures/bitswap/hidden-idle-flush.jsonl \
    && printf '%s\n' \
    '{"seq":1,"op":"want","cid":"bafyAA0000000000000000000000000000000000000000000000000000000000000001","priority":30}' \
    '{"seq":2,"op":"want","cid":"bafyAA0000000000000000000000000000000000000000000000000000000000000002","priority":4}' \
    '{"seq":3,"op":"cancel","cid":"bafyAA0000000000000000000000000000000000000000000000000000000000000002"}' \
    '{"seq":4,"op":"merge_wants","wants":[{"cid":"bafyAA0000000000000000000000000000000000000000000000000000000000000002","priority":2}]}' \
    > /opt/verifier-fixtures/bitswap/hidden-priority-head.jsonl

RUN sed -i 's/\r$//' /app/scripts/*.sh \
    && chmod +x /app/scripts/*.sh \
    && go build -mod=readonly -o /usr/local/bin/bswapd ./cmd/bitswapctl
