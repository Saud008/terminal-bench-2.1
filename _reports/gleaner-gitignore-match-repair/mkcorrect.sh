#!/bin/bash
# Builds /tmp/gl-correct-app = environment/app with src replaced by correct-src, compiles to /tmp/gl-target/release
set -euo pipefail
R="/mnt/c/Users/masau/Downloads/Terminus-2nd edition (1)"
D="$R/_reports/gleaner-gitignore-match-repair"
T="$R/gleaner-gitignore-match-repair/gleaner-gitignore-match-repair"
rm -rf /tmp/gl-correct-app && cp -r "$T/environment/app" /tmp/gl-correct-app
rm -rf /tmp/gl-correct-app/src && cp -r "$D/correct-src" /tmp/gl-correct-app/src
bash "$D/build.sh" /tmp/gl-correct-app /tmp/gl-target/release
bash "$D/build.sh" "$T/environment/app" /tmp/gl-bug
