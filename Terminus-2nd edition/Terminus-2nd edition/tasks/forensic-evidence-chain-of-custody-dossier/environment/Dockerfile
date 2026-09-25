FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

LABEL org.opencontainers.image.title="forensic-evidence-chain-of-custody-dossier"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip tmux asciinema \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir --break-system-packages \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

COPY Cargo.toml ./
COPY src ./src
COPY config ./config
COPY docs ./docs
COPY catalog ./catalog
COPY fixtures ./fixtures
COPY scripts ./scripts
COPY hidden /opt/verifier-fixtures/forensic

RUN mkdir -p /app/var /app/output /app/bin \
    && sed -i 's/\r$//' /app/scripts/*.sh \
    && chmod +x /app/scripts/*.sh \
    && cargo generate-lockfile \
    && cargo build --release --locked \
    && cp /app/target/release/rvk9 /app/bin/rvk9

ENV PYTHONPATH="/app/scripts"
ENV PATH="/app/bin:/usr/local/cargo/bin:${PATH}"
