# Engineering problem contract

Operators need a numerical calibration atlas that correlates per-sensor header timelines against a rosbag reference topic. The skew-cal tool materializes manifest latch, normalized message ledgers, median-anchor synchronization windows, and least-squares drift slopes as deterministic JSON.

The verifier exercises topic remap persistence, strict monotonic header guards, duplicate msg index supersession by relay_pass, reference-topic anchoring (not global minimum stamps), stream gap tallies, and centered drift regression signs.

This task profiles multi-stream clock skew and synchronization windows for mobile robotics field-log playback per /app/docs/rosbag-calibration-lattice.md. It does not gap-fill MIDI charts, evaluate QoS deadlines, bundle ICC gamut cubes, or emit SQLite message tables.
