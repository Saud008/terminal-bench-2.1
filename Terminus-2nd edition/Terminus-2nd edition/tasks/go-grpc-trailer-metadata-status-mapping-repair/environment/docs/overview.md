# Overview

`grpcfaultd` is a fault-injection gRPC server for exercising metadata trailers, rich status details, cancellation mapping, receive limits, and unary/stream error shaping. Configure catalogs through the admin RPC, then probe inject endpoints with `grpcurl` or `frameprobe`.
