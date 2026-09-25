#!/bin/bash
echo "=== liora ==="
find '/mnt/d/Terminus---liora-main' -iname '*nmea*' 2>/dev/null | head -40
echo "=== Terminus-2nd edition tree depth 3 ==="
find '/mnt/d/Terminus-2nd edition' -maxdepth 3 -type d 2>/dev/null | head -60
echo "=== any test_outputs with nmea on D ==="
find /mnt/d -name test_outputs.py 2>/dev/null | while read -r f; do
  grep -ql nmeapipeline "$f" 2>/dev/null && echo "$f $(wc -l < "$f")"
done
echo "=== any Dockerfile with nmeapipeline on D ==="
find /mnt/d -name Dockerfile 2>/dev/null | while read -r f; do
  grep -ql nmeapipeline "$f" 2>/dev/null && echo "$f"
done
echo "=== zip sizes nmea on D ==="
find /mnt/d -iname '*nmea*.zip' 2>/dev/null -exec ls -la {} \;
echo DONE
