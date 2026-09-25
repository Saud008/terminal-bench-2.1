# Submission explanations — go-grpc-trailer-metadata-status-mapping-repair

**Task folder:** tasks/go-grpc-trailer-metadata-status-mapping-repair/
**Platform form only** — not in upload zip.

## Difficulty Explanation

Agents must align three cooperating layers under /app/internal/grpc without editing protected docs or fixtures. Status mapping, trailer interceptors, and receive-size guards interact so fixing cancellation alone still leaves trailer metadata leaking into headers on streaming RPCs. Seed-scoped catalog keys mean agents cannot hard-code trailer or detail field names from a single example run.

## Solution Explanation

The oracle restores statusmap.go to map context cancellation correctly and attach ErrorInfo details for rich status responses. It replaces trailer interceptors so SetTrailer values stay in trailers for unary and server-streaming calls instead of leaking into headers. The recv_limit interceptor is fixed so only protobuf payload bytes count toward MaxUserMessageBytes. Rebuilding grpcfaultd after those patches satisfies the contract-driven catalog probes exercised by frameprobe.

## Verification Explanation

Pytest rebuilds grpcfaultd from agent code and drives frameprobe and grpcurl as external CLI processes. An independent reference_status module computes expected codes, trailer keys, and detail reasons per seed. Tests verify header and trailer separation on unary and streaming trailer-split cases, check protected path SHA256 digests for docs and fixtures, and run hidden seeds from /opt/verifier-fixtures/grpc/hidden/.
