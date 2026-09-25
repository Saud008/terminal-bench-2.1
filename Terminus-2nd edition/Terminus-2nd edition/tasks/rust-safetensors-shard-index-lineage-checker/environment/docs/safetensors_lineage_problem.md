# Engineering problem contract

xr7 validates multi-shard safetensors weight catalogs for ML release governance. Unlike chunked array consolidators, this tool reasons about binary tensor headers, LoRA parent hash binding, and per-shard payload fingerprints. Verifier math recomputes dtype byte spans and payload-relative offsets from raw safetensors bytes.
