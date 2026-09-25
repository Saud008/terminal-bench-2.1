FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

LABEL org.opencontainers.image.title="airport-baggage-misroute-rootcause-atlas" \
      org.opencontainers.image.description="Airport baggage misroute root-cause atlas verifier environment" \
      org.opencontainers.image.vendor="anonymous"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip tmux asciinema patch \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir --break-system-packages \
    pytest==9.0.3 \
    pytest-json-ctrf==0.5.0

COPY Cargo.toml Cargo.lock ./
COPY src ./src
COPY ingress_normalizer ./ingress_normalizer
COPY belt_matrix ./belt_matrix
COPY gap_evaluator ./gap_evaluator
COPY suppress_filter ./suppress_filter
COPY cause_rank ./cause_rank
COPY output_facet ./output_facet
COPY weight_decoy ./weight_decoy
COPY model ./model
COPY config ./config
COPY docs ./docs
COPY fixtures ./fixtures
COPY scripts ./scripts
COPY tools ./tools
COPY hidden /opt/verifier-fixtures/bag-atlas

RUN mkdir -p /app/state/hub-latch /app/work/scan-ledger /app/work/route-lattice /app/output /app/bin \
    && sed -i 's/\r$//' /app/scripts/*.sh \
    && chmod +x /app/scripts/reset-workspace.sh \
    && cargo build --release --locked \
    && cp /app/target/release/bag-atlas /app/bin/bag-atlas

ENV PATH="/app/bin:/usr/local/cargo/bin:${PATH}"
