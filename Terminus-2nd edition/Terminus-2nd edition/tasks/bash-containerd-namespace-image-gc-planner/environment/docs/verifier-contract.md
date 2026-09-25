# Verifier contract

Tests invoke /app/lib/cli.sh via bash subprocess.

Reference math is implemented independently in pytest and must not import ctrgc modules.

Hidden fixture trees may appear under verifier-only directories configured by the harness.
