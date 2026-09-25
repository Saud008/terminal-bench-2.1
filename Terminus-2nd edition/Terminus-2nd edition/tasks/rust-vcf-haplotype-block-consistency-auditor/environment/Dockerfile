FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

LABEL org.opencontainers.image.title="rust-vcf-haplotype-block-consistency-auditor" \
      org.opencontainers.image.description="VCF haplotype block consistency auditor verifier environment" \
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
COPY gt_parser ./gt_parser
COPY alt_split ./alt_split
COPY phase_wiring ./phase_wiring
COPY cohort_lineage ./cohort_lineage
COPY sample_matrix ./sample_matrix
COPY edge_list ./edge_list
COPY anomaly_score ./anomaly_score
COPY vcf_scan ./vcf_scan
COPY decoy_pca ./decoy_pca
COPY model ./model
COPY config ./config
COPY docs ./docs
COPY fixtures ./fixtures
COPY scripts ./scripts

RUN mkdir -p /app/state/sample-phase-matrix /app/work/block-edge-list /app/output /app/bin \
    && sed -i 's/\r$//' /app/scripts/*.sh /app/fixtures/build_fixtures.py \
    && chmod +x /app/scripts/reset-workspace.sh /app/fixtures/build_fixtures.py \
    && python3 /app/fixtures/build_fixtures.py --seed 4242 --out-dir /app/fixtures \
    && cargo build --release --locked \
    && cp /app/target/release/vcfaud /app/bin/vcfaud

ENV PATH="/app/bin:/usr/local/cargo/bin:${PATH}"
