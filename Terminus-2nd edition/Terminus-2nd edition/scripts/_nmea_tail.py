def write_tests(nmea_line) -> None:
    w(
        TESTS / "test.sh",
        """#!/usr/bin/env bash
set -uo pipefail

export PATH="/usr/local/cargo/bin:/opt/verifier-venv/bin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH}"
TEST_DIR="${TEST_DIR:-/tests}"

mkdir -p /logs/verifier /app/output /app/state
echo 0 > /logs/verifier/reward.txt
printf '{"version":"1.0.0","results":[]}\\n' > /logs/verifier/ctrf.json

cd /app || {
  echo 0 > /logs/verifier/reward.txt
  exit 1
}

set +e
bash /app/scripts/reset-state.sh
RESET_RC=$?
cargo build --release --locked -p nmeapipeline
BUILD_RC=$?
install -m 0755 /app/target/release/nmeapipeline /usr/local/bin/nmeapipeline
INSTALL_RC=$?
[ "$RESET_RC" -eq 0 ] && [ "$BUILD_RC" -eq 0 ] && [ "$INSTALL_RC" -eq 0 ] && \\
  /opt/verifier-venv/bin/python3 -m pytest -o cache_dir=/tmp/pytest_cache \\
    --ctrf /logs/verifier/ctrf.json "${TEST_DIR}/test_outputs.py" -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
""",
    )
    part2 = TESTS / "hidden_bundles" / "duplicate-replay-part2.nmea"
    if not part2.exists():
        w(
            part2,
            "\n".join(
                [
                    nmea_line("$GPGSV,2,1,08,22,50,090,50,05,20,310,44"),
                    nmea_line("$GNGSV,2,2,08,33,06,122,42,04,12,311,43"),
                ]
            )
            + "\n",
        )


if __name__ == "__main__":
    main()
