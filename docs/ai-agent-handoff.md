# AI agent handoff

## Identity

`nodeio-serve` is the HTTP and gRPC ingress. Python 3.13 and 3.14.
Public repository `NjordLabs/nodeio-serve`. The image is an example
and is not published. [`v0.3.0`](https://github.com/NjordLabs/nodeio-serve/releases/tag/v0.3.0)
is the GitHub Release. The wheel sha256 is written when the release
workflow uploads it. That workflow pins pydevops `3.11.3`
(`8b0d7d08`). Quality jobs stay on pydevops `3.11.1` (`efef9824`).

## Scope

Pins: guardrails `1.17.1` (`8508e936`), scaffold `1.14.3` (`1fca8a3b`), pydevops `3.11.1` (`efef9824`), commondevops `v6.12.0` (`ff65e7ef`).

`GET /health`, `POST /v1/run`, and generated `nodeio.v1.GraphService/Run`.
The handler is injected. The engine stays in nodeio. The `grpc` extra
(`grpcio`, `protobuf`) is optional. HTTP does not depend on it.
`create_ingress` shares one `asyncio.Semaphore` between the two
ingresses. Responses go through `nodeio_serve.codec`.

## Commands

```bash
sh scripts/check-ci-local.sh
uv run --python 3.14 --group dev --extra grpc pytest -q
uv sync --frozen --group dev --extra grpc --python 3.13
sh scripts/check-ci-docker.sh
docker build -t nodeio-serve:local .
```

Regenerate the image lock when `uv.lock` changes:

```bash
uv export --frozen --no-dev --no-emit-project --no-header -o requirements.txt
```

`scripts/check-ci-local.sh` diffs that file. The image installs it with
`pip install --require-hashes`, then copies this package into
site-packages. The header is omitted because it records the output
path.

## Known pitfalls

The container workflow sets `push_handoff: false` and
`scan_local: true`. The example image is not published. The lint job
passes `GHCR_READ_TOKEN` as `container_token` so infra lint and the
secrets scan can pull private `ghcr.io/pirlruc/ci-lint`.

The build and lint callers pin containerdevops `6.10.0`
(`b1cf0dead`). Docker Dependabot is in the `all-dependencies` group.

Hand-written `jsonio` and `state` live in the package. Generated stubs live in `src/nodeio_serve/_gen` and are passed as `generated_paths`. The image does not authenticate callers.

The generated stub requires `grpcio>=1.85.3` and `protobuf>=7.35.1`.
`protobuf` is in the extra because the generated module imports it.
The HTTP install does not.

Uvicorn `timeout_graceful_shutdown` is 30 seconds. The lifespan only
yields. It does not cancel a handler.

`requirements.txt` is not updated by the uv Dependabot group. The
local CI diff is the check.

## Suggested next work

PyPI publish stays open (`SERVE-001-T2`). The example image stays
unpublished. `SERVE-003` is done: container lint receives
`GHCR_READ_TOKEN`.

## Recent history

- feat(ingress): cap bodies before buffering and serve generated Run
- ci: hash-lock the image and pin the quality workflows
- docs: record 0.2.0
- release: tag v0.2.0
- chore(release): set 0.3.0 and pin the release workflow to pydevops 3.11.3

*Last updated: 2026-11-26.*
