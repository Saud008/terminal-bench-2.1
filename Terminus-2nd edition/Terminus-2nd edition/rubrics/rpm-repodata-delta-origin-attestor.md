# Platform rubric — rpm-repodata-delta-origin-attestor

**Task folder:** tasks/rpm-repodata-delta-origin-attestor/

Agent verifies repomd checksum types with matching SHA-256 or SHA-1 algorithms per data entry, +3
Agent formats NEVRA keys with explicit epoch prefix including epoch zero, +3
Agent ranks package lineage using RPM EVRA segment ordering within name and arch groups, +3
Agent resolves modulemd default_stream from stream_name not profiles list ordering, +3
Agent rejects stale mirror snapshots when repo_revision lags repomd revision, +3
Agent binds mirror captured_at against repomd_generated timestamp from manifest, +2
Agent exports origin_digest as sha256 over canonical sorted digest payload, +3
Agent reads mirror_snapshot_valid from staging during export without reopening mirror files, +2
Agent writes ingest staging snapshot before export attestation from staging only, +2
Agent leaves lib/decoy off ingest and export hot path, +1
Agent hashes repomd metadata with SHA-1 when checksum type is sha256, -3
Agent ranks package versions using plain ASCII sort on version strings, -3
Agent picks module default streams from first profiles entry instead of stream_name, -3
Agent accepts mirror snapshots based only on wall-clock age without revision match, -3
Agent emits md5 origin_digest or unsorted digest package lists, -2
Agent re-parses repomd.xml from ingest directory during export attestation, -2
