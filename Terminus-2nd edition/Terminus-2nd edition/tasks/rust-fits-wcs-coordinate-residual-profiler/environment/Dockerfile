FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

LABEL org.opencontainers.image.title="rust-fits-wcs-coordinate-residual-profiler" \
      org.opencontainers.image.description="FITS WCS coordinate residual profiler verifier environment" \
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
COPY fcard_lex ./fcard_lex
COPY wmeter_hdr ./wmeter_hdr
COPY tan_pixsky ./tan_pixsky
COPY det_rows ./det_rows
COPY gc_match ./gc_match
COPY src_flags ./src_flags
COPY rms_atlas ./rms_atlas
COPY plate_decoy ./plate_decoy
COPY model ./model
COPY config ./config
COPY docs ./docs
COPY fixtures ./fixtures
COPY scripts ./scripts
COPY support ./support
COPY hidden /opt/verifier-fixtures/wcspfit

RUN mkdir -p /app/state/wcs-cache /app/work/detection-buffer /app/work/xmatch-buffer /app/output /app/bin \
    && sed -i 's/\r$//' /app/scripts/*.sh \
    && chmod +x /app/scripts/reset-workspace.sh \
    && cargo generate-lockfile \
    && cargo build --release --locked \
    && cp /app/target/release/wcspfit /app/bin/wcspfit

ENV PATH="/app/bin:/usr/local/cargo/bin:${PATH}"
