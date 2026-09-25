# Interceptor order

Unary chain (outer to inner):

1. Receive-size guard
2. Trailer/header merge guard

Streaming chain:

1. Trailer/header merge guard

Interceptors must not weaken status mapping performed in `/app/internal/grpc/statusmap.go`.
