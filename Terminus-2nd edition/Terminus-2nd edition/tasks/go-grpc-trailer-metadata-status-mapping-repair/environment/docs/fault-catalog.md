# Fault catalog

Configure with:

```text
grpcurl -plaintext -d '{"seed":"SEED"}' 127.0.0.1:50051 fault.v1.Admin/ConfigureCatalog
```

| Case ID | Mode | Behavior |
|---------|------|----------|
| `trailer-split` | unary/stream | Sets seed-scoped trailer metadata; trailers must not appear in response headers for either mode |
| `status-details` | unary | Returns `FailedPrecondition` with `ErrorInfo` details |
| `ctx-cancel` | unary | Surfaces context cancellation |
| `recv-limit-body` | unary | Enforces payload receive cap |
| `unary-shape` | unary | Invalid argument shaped for unary clients |
| `stream-shape` | stream | Invalid argument shaped for streaming clients |

Seeds in `/app/fixtures/seeds.json` permute trailer and detail metadata keys only.
