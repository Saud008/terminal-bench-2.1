# Platform rubric — git-packfile-delta-chain-packctl

**Task folder:** tasks/git-packfile-delta-chain-packctl/

Agent resolves delta chains in longest-base-first topological order before export, +3
Agent measures OFS_DELTA copy offsets from the pre-image base window origin, +3
Agent validates ref_delta base kinds and rejects commit or tag bases before lookup, +3
Agent isolates zlib inflate buffers per chain link without shared scratch reuse, +3
Agent rolls up total_inflated_bytes from final inflated payload sizes only, +2
Agent starts ref_delta patch application from an empty output buffer, +2
Agent reads /app/state/pack-stage.json in resolve export without re-parsing catalog.json, +2
Agent rebuilds packctl with cargo in test.sh after editing resolve or export modules, +2
Agent skips invalid ref_delta traps pointing at forbidden base kinds in hidden packs, +2
Agent leaves src/decoy off the ingest and resolve export hot path, +1
Agent walks delta chains depth-first leaf before base objects, -3
Agent shifts OFS_DELTA windows using post-patch tail heuristics, -3
Agent dereferences ref_delta bases before kind validation allows commit parents, -3
Agent reuses one zlib scratch buffer across multi-hop delta inflates, -3
Agent sums intermediate delta compressed_size values in export rollup, -2
