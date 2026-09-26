FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac

RUN apt-get update \
    && apt-get install -y --no-install-recommends asciinema ca-certificates python3 python3-venv tmux xxd \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/pytools \
    && /opt/pytools/bin/pip install --no-cache-dir pytest==8.4.1 pytest-json-ctrf==0.3.5

ENV GOTOOLCHAIN=local \
    CGO_ENABLED=0

# Login shells reset PATH from /etc/profile, which drops /usr/local/go/bin.
RUN ln -s /usr/local/go/bin/go /usr/local/go/bin/gofmt /usr/local/bin/

WORKDIR /app
COPY app/ /app/
RUN go build -o /dev/null ./cmd/shiftclock
