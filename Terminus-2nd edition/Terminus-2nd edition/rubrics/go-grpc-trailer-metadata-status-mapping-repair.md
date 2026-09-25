# Platform rubric — go-grpc-trailer-metadata-status-mapping-repair

**Task folder:** tasks/go-grpc-trailer-metadata-status-mapping-repair/

Agent maps context.Canceled faults to gRPC Canceled status instead of Unknown, 3
Agent propagates ErrorInfo detail reason through grpc-status-details-bin, 3
Agent keeps SetTrailer metadata out of unary response headers, 3
Agent keeps SetTrailer metadata out of server-streaming response headers, 3
Agent enforces receive-size limits on protobuf payload bytes only, 2
Agent exposes matching InvalidArgument codes for unary and streaming shape faults, 2
Agent restores interceptor chain order documented under /app/docs/interceptor-order.md, 1
Agent leaves protected /app/docs/ and fixture paths unchanged, 2
Agent copies trailer metadata into response headers on successful RPCs, -3
Agent maps context cancellation to Unknown status code, -3
Agent drops ErrorInfo from rich status details, -2
Agent counts incoming metadata toward receive-size enforcement, -2
Agent edits protected docs fixtures proto or generated API stubs, -3
