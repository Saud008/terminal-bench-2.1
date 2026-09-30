#!/bin/bash
# For each src file that differs between correct-src and environment/app/src: build correct tree with that one file reverted, compare vs cases.json
set -uo pipefail
R="/mnt/c/Users/masau/Downloads/Terminus-2nd edition (1)"
D="$R/_reports/gleaner-gitignore-match-repair"
T="$R/gleaner-gitignore-match-repair/gleaner-gitignore-match-repair"
cd "$D/correct-src"
for f in $(find . -name '*.rs' | sort); do
  if ! cmp -s "$f" "$T/environment/app/src/$f"; then
    rm -rf /tmp/gl-abl && cp -r "$T/environment/app" /tmp/gl-abl && rm -rf /tmp/gl-abl/src && cp -r "$D/correct-src" /tmp/gl-abl/src
    cp "$T/environment/app/src/$f" "/tmp/gl-abl/src/$f"
    bash "$D/build.sh" /tmp/gl-abl /tmp/gl-abl-bin >/dev/null
    echo "### reverted $f"
    docker run --rm -v "$D":/r:ro -v /tmp/gl-abl-bin:/b:ro -v "$T/tests":/t:ro gleaner-dev python3 /r/check_cases.py /t/cases.json /b/gleaner | grep FAIL || echo "   !!! NO FAILING GROUP"
  fi
done
