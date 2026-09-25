FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

LABEL org.opencontainers.image.title="rust-rosbag-topic-clock-skew-indexer" \
      org.opencontainers.image.description="ROS bag topic clock skew indexer verifier environment" \
      org.opencontainers.image.vendor="anonymous"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip tmux asciinema \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir --break-system-packages \
    pytest==9.0.3 \
    pytest-json-ctrf==0.5.0

COPY Cargo.toml Cargo.lock ./
COPY src ./src
COPY kennel_io ./kennel_io
COPY hopf_weave ./hopf_weave
COPY order_gate ./order_gate
COPY ruelle_pq ./ruelle_pq
COPY relay_rank ./relay_rank
COPY peskin_pq ./peskin_pq
COPY tf_decoy ./tf_decoy
COPY model ./model
COPY config ./config
COPY docs ./docs
COPY fixtures ./fixtures
COPY scripts ./scripts
COPY tools ./tools
COPY hidden /opt/verifier-fixtures/skew-cal

RUN mkdir -p /app/state/manifest-latch /app/work/timeline-ledger /app/work/sync-lattice /app/output /app/bin \
    && sed -i 's/\r$//' /app/scripts/*.sh \
    && chmod +x /app/scripts/reset-workspace.sh \
    && cargo build --release --locked \
    && cp /app/target/release/skew-cal /app/bin/skew-cal

ENV PATH="/app/bin:/usr/local/cargo/bin:${PATH}"
