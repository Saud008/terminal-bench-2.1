FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema \
        python3 \
        python3-venv \
        tmux \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/pytools \
    && /opt/pytools/bin/pip install --no-cache-dir pytest==8.4.1 pytest-json-ctrf==0.3.5

# Keep an interactive terminal usable when a pasted snippet enables errexit.
RUN printf '\ncase $- in *i*) trap '"'"'exec bash -i'"'"' EXIT ;; esac\n' >> /etc/bash.bashrc

# Login shells reset PATH through /etc/profile; keep the toolchain reachable.
RUN printf 'export PATH=/usr/local/cargo/bin:$PATH\n' > /etc/profile.d/cargo.sh

WORKDIR /app

COPY app/ /app/

RUN cargo build --release --offline \
    && ln -s /app/target/release/crumbjar /usr/local/bin/crumbjar
