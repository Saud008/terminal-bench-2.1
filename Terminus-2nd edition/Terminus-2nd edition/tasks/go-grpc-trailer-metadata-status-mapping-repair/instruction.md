The grpcfaultd server at /app/cmd/grpcfaultd exposes fault-injection RPCs for unary and server-streaming calls. Extend the status mapping and interceptor subsystem under /app/internal/grpc/ to validate fault metadata contracts and preserve trailer/header invariants across unary and server-streaming probes.

The server listens on 127.0.0.1:50051. Fault injection is configurable through the admin RPC described in /app/docs/fault-catalog.md. Metadata rules, status mapping, interceptor expectations, and hidden verifier fixture rules are defined in /app/docs/fault-catalog.md, /app/docs/grpc-status.md, /app/docs/interceptor-order.md, and /app/docs/contract.md.

Implement the gRPC status mapping and interceptor chain under /app/internal/grpc/ so rebuilt binaries satisfy the contract. Do not edit /app/docs/, /app/fixtures/, /app/proto/, /app/api/, or /tests/.
