# gRPC status and metadata reference

Clients observe:

| Field | Source |
|-------|--------|
| Status code | gRPC status on RPC completion |
| Message | Status message string (not verified by contract tests) |
| Headers | Initial metadata (`grpc.Header`) |
| Trailers | Trailing metadata (`grpc.Trailer`) |
| Detail reason | First `google.rpc.ErrorInfo.reason` in status details |

`grpc-status-details-bin` carries protobuf-encoded `google.rpc.Status` details when present.
