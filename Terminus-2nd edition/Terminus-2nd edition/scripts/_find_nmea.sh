#!/bin/bash
echo "=== Dockerfile containing nmeapipeline ==="
find /home/saud -name Dockerfile 2>/dev/null | while read -r f; do
  grep -ql nmeapipeline "$f" 2>/dev/null && echo "$f"
done
echo "=== test_outputs with NmeaMultipart ==="
find /home/saud -name test_outputs.py 2>/dev/null | while read -r f; do
  grep -ql NmeaMultipart "$f" 2>/dev/null && echo "$f"
done
echo "=== solve.sh with nmeapipeline ==="
find /home/saud -name solve.sh 2>/dev/null | while read -r f; do
  grep -qlE 'nmeapipeline|golden_reconcile' "$f" 2>/dev/null && echo "$f"
done
echo "=== Cargo.toml nmeapipeline ==="
find /home/saud -name Cargo.toml 2>/dev/null | while read -r f; do
  grep -ql nmeapipeline "$f" 2>/dev/null && echo "$f"
done
echo "=== large nmea zips ==="
find /home/saud -iname '*nmea*.zip' -size +50k 2>/dev/null
echo "=== dirs named nmea0183 ==="
find /home/saud -type d -name 'nmea0183*' 2>/dev/null
echo "=== harbor jobs with nmea ==="
find /home/saud -path '*jobs*' -name 'test-stdout.txt' 2>/dev/null | while read -r f; do
  grep -ql NmeaMultipart "$f" 2>/dev/null && echo "$f"
done
echo DONE
