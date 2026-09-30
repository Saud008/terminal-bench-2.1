FROM public.ecr.aws/docker/library/gcc:13-bookworm@sha256:930f2ebe239275fa67226654cb79273ea34eee672ae61c8a39f689c37fb7ac5c

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema \
        python3 \
        python3-venv \
        tmux \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/pytools \
    && /opt/pytools/bin/pip install --no-cache-dir pytest==8.4.1 pytest-json-ctrf==0.3.5

WORKDIR /app

COPY app/ /app/

RUN make \
    && ln -s /app/build/zonec /usr/local/bin/zonec
