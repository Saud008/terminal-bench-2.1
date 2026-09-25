# Monotonic stamp contract

After remap and duplicate resolution, messages group by remapped topic sorted by header_stamp_ns ascending. Each topic must have strictly increasing header_stamp_ns values. Equal consecutive header_stamp_ns values fail timeline normalization. When two sensors collapse into the same remapped topic, header_stamp_ns progression is evaluated independently per topic stream.
