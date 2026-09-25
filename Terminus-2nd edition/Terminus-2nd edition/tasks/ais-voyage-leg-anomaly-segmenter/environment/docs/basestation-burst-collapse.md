# Base-station burst dedupe

After MMSI dedupe, collapse burst duplicates from the same base station. Rows burst-duplicate when they share mmsi and station, ts_epoch differs by at most AIS_BURST_MS milliseconds (default 500), and lat and lon each differ by at most 0.0001 degrees. Keep the lowest seq in each burst group. Count removed rows toward burst_duplicate in atlas anomalies.

Burst collapse runs only during feed.
