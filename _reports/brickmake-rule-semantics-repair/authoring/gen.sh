#!/bin/bash
# gen.sh <task-dir> [extra.json]: re-derive cases.json expectations with GNU make 4.3 (debian bookworm)
T=$(realpath "$1"); A=$(dirname "$(realpath "$0")"); EXTRA=${2:+/a/$(basename "$2")}
docker run --rm -v "$T/tests:/tests:ro" -v "$A:/a:ro" public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac bash -c "
apt-get update -qq >/dev/null && apt-get install -y -qq make python3 >/dev/null 2>&1
make --version | head -1
python3 /a/gen_expect.py /tests/cases.json $EXTRA"
