bash /app/scripts/reset-state.sh

cargo build --offline --locked -p nmeapipeline
install -m 0755 target/debug/nmeapipeline /usr/local/bin/nmeapipeline

set +e