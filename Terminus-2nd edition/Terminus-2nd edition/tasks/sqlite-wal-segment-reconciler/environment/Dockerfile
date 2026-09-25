FROM public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash=5.2.15-2+b13 \
        ca-certificates=20230311+deb12u1 \
        tmux=3.3a-3 \
        asciinema=2.2.0-1 \
        python3=3.11.2-1+b1 \
        python3-pip=23.0.1+dfsg-1 \
        python3-venv=3.11.2-1+b1 \
        sqlite3=3.40.1-2+deb12u2 \
        xxd=2:9.0.1378-2+deb12u2 \
        coreutils=9.1-1 \
        gawk=1:5.2.1-2 \
        make=4.3-4.1 \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir \
        pytest==9.0.3 \
        pytest-json-ctrf==0.5.0

WORKDIR /app

COPY Makefile /app/
COPY README.md /app/
COPY cli/ /app/cli/
COPY lib/ /app/lib/
COPY docs/ /app/docs/
COPY scripts/ /app/scripts/
COPY tools/ /app/tools/
COPY state/ /app/state/

RUN make install \
    && mkdir -p /app/state /app/output /app/fixtures/seed \
    && chmod +x /app/tools/init_state.sh /app/tools/build_hidden_fixtures.py \
    && /app/tools/init_state.sh \
    && python3 /app/tools/build_hidden_fixtures.py

ENV PATH="/app/bin:${PATH}"
