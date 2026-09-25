# Manifest format

Each manifest is a JSON document under the manifest directory. Files are processed in lexicographic path order. A manifest exposes manifest_id, base_model_hash, expected_base_model_hash, and a shards array.

Each shard entry names shard_file relative to the shard root and lists tensor specs with name, dtype, and shape. Dtype strings follow safetensors naming: F32, F16, BF16, I32, I64, U8.
