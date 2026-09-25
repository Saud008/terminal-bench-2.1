# grpcfaultd contract

## Admin catalog seeding

`fault.v1.Admin/ConfigureCatalog` with non-empty `seed` activates the catalog described in `/app/docs/fault-catalog.md`. Fault metadata keys vary per seed; behavioral rules do not.

## Header and trailer separation

Trailing metadata set with `grpc.SetTrailer` must appear only in response trailers. Values must not be copied into response headers. Incoming header keys must remain visible separately from trailer keys on successful unary and server-streaming RPCs.

## Rich error details

Errors created with `ErrorInfo` details must propagate `grpc-status-details-bin` to clients. `DetailReason` observed by clients must equal the configured reason string for the active seed. Status message text is not part of the contract; verifier checks gRPC status codes and `DetailReason` only.

## Context cancellation mapping

`context.Canceled` faults must surface gRPC code `Canceled`, never `Unknown`.

## Receive size limits

`MaxUserMessageBytes` applies to protobuf message payload bytes only. Incoming metadata size must not count toward the receive limit enforced by interceptors.

## Unary and streaming error shaping

For the same logical status code and message, unary and server-streaming inject faults must expose identical gRPC status codes to clients. Do not remap unary faults to `Internal` while leaving streaming faults untouched.

## Protected paths

Do not edit `/app/docs/`, `/app/fixtures/`, `/app/proto/`, `/app/api/`, or `/tests/`.

## Hidden verifier fixtures

Pytest may load alternate catalog seeds from `/opt/verifier-fixtures/grpc/hidden/`. Hidden probes use the same status, trailer, and detail rules as bundled fixtures.
