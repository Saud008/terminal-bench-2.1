FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

LABEL org.opencontainers.image.title="rust-bgp-route-flap-dampening-simulator" \
      org.opencontainers.image.description="BGP route flap dampening simulator verifier environment" \
      org.opencontainers.image.vendor="anonymous"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip tmux asciinema \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir --break-system-packages \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

COPY Cargo.toml Cargo.lock ./
COPY src ./src
COPY lattice ./lattice
COPY timeline ./timeline
COPY peers ./peers
COPY reports ./reports
COPY runloop ./runloop
COPY model ./model
COPY decoy ./decoy
COPY docs ./docs
COPY fixtures ./fixtures
COPY scripts ./scripts

RUN mkdir -p /app/state /app/output /app/bin \
    && cargo build --release --locked \
    && cp /app/target/release/rdampctl /app/bin/rdampctl

ENV PATH="/app/bin:${PATH}"
