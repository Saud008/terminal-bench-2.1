# Wireclock CLI

Build wireclock with go build -mod=readonly -o /usr/local/bin/wireclock ./cmd/wireclock.
Run wireclock serve --listen 127.0.0.1:9090 --db /app/data/oidguard.db.
The service exposes health, mint, wire-document, intake, resume, and statistics endpoints on the selected listener.
