#!/usr/bin/env bash
set -euo pipefail
rm -rf /app/output /app/state
mkdir -p /app/output /app/state
if [ -d /opt/demo-seed ]; then
  rm -rf /app/projects/demo/.libs /app/projects/demo/install /app/projects/demo/sub
  mkdir -p /app/projects/demo/.libs /app/projects/demo/install/lib /app/projects/demo/sub
  cp -a /opt/demo-seed/.libs/. /app/projects/demo/.libs/
  cp -a /opt/demo-seed/install/. /app/projects/demo/install/
  cp -a /opt/demo-seed/sub/. /app/projects/demo/sub/
fi
