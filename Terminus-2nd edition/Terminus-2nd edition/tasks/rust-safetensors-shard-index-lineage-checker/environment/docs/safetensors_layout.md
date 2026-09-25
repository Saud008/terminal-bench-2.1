# Safetensors on-disk layout

A shard file begins with an eight byte little endian unsigned integer giving the JSON header byte length. The JSON header maps tensor names to dtype, shape, and data_offsets relative to the start of the payload section that follows the header.

data_offsets are half open intervals within the payload bytes only. Validation must never compare offsets against the whole file size including the header prefix.
