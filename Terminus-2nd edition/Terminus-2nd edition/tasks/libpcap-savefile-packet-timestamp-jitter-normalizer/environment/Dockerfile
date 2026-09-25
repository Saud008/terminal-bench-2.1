FROM --platform=linux/amd64 public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

LABEL org.opencontainers.image.title="libpcap-savefile-packet-timestamp-jitter-normalizer"
LABEL org.opencontainers.image.description="Terminus task environment for pcapjitter libpcap timeline normalizer"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema \
        ca-certificates \
        python3 \
        python3-pip \
        python3-venv \
        tmux \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir \
        pytest==9.0.3 \
        pytest-json-ctrf==0.5.0

ENV PATH="/usr/local/cargo/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
ENV CARGO_INCREMENTAL=0

WORKDIR /app
COPY . /app/

RUN python3 /app/fixtures/build_pcap_fixtures.py \
    && mkdir -p /opt/verifier-fixtures/pcap /app/state /app/output \
    && cp -a /app/fixtures/hidden/. /opt/verifier-fixtures/pcap/ \
    && rm -rf /app/fixtures/hidden \
    && cargo build --locked -p pcapjitter
