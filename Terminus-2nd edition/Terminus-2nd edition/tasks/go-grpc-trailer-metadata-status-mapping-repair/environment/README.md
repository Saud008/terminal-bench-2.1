# grpcfaultd

gRPC fault-injection server for exercising trailer metadata, rich error details, context cancellation mapping, receive limits, and unary/stream status shaping.

- Binary: `go build -mod=readonly -o /usr/local/bin/grpcfaultd ./cmd/grpcfaultd`
- Contract: `/app/docs/contract.md`
- Admin catalog seeding: `/app/docs/fault-catalog.md`
