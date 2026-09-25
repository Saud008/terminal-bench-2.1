# CLI reference

## grpcfaultd

```
grpcfaultd --listen 127.0.0.1:50051
```

## grpcurl (reflection enabled)

```text
grpcurl -plaintext 127.0.0.1:50051 list
grpcurl -plaintext -d '{"seed":"grpc-seed-7"}' 127.0.0.1:50051 fault.v1.Admin/ConfigureCatalog
grpcurl -plaintext -d '{"case_id":"trailer-split"}' 127.0.0.1:50051 fault.v1.Inject/UnaryInject
```

## frameprobe

```text
frameprobe --addr 127.0.0.1:50051 --seed SEED --case CASE --mode unary
```
