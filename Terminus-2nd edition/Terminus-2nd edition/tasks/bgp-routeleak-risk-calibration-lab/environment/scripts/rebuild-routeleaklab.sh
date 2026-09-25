#!/usr/bin/env bash
set -euo pipefail
cd /app
export PYTHONPATH="/app${PYTHONPATH:+:$PYTHONPATH}"
cat > /usr/local/bin/routeleaklab <<'EOF'
#!/usr/bin/env bash
export PYTHONPATH="/app${PYTHONPATH:+:$PYTHONPATH}"
exec python3 -m routeleak_lab "$@"
EOF
chmod +x /usr/local/bin/routeleaklab
