# Changelog

## Unreleased

- Hand-written modules sit in the package. Generated stubs sit in `_gen`.
- The gRPC receive cap includes framing headroom. Abort does not return.
- The example image has no authentication. The documented run adds a `/tmp` tmpfs.

## 0.2.0 - 2026-11-22

- The HTTP body cap is applied before the payload is buffered.
- HTTP and gRPC responses use one JSON encoder. A value that is not
  JSON becomes an error response.
- The process sets a graceful shutdown timeout. The lifespan does not
  cancel a handler on its own.
- The example image installs hash-locked requirements.
- `Run` is a generated grpcio.aio servicer. It is an optional `grpc`
  extra and shares the HTTP concurrency limit. The image does not
  install that extra.

## 0.1.0 - 2026-11-22

- HTTP `GET /health` and `POST /v1/run` with a body cap and a
  concurrency limit.
- A gRPC `Run` servicer that uses the same caps.
- Example image. The image is not published.
