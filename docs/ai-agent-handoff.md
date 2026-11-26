# AI agent handoff

## Identity

`nodeio-serve` is the HTTP and gRPC ingress. Python 3.13 and 3.14.
Public repository `NjordLabs/nodeio-serve`. The image is an example
and is not published. [`v0.2.0`](https://github.com/NjordLabs/nodeio-serve/releases/tag/v0.2.0)
is the GitHub Release.
The wheel sha256 is
`7efbda50dd22e16160f62863de29a66c0074eaf453d6ab69c90327ff76261908`.

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
sets `run_infra_lint: false` and `run_secrets_scan: false` because
those jobs pull private `ghcr.io/pirlruc/ci-lint`, which this
repository's token cannot read. Dockerfile lint and the build still
run.

`container-lint.yml` exists at the same containerdevops pin the build
caller uses (`4d5c00e20786811f740b70ee9d46832fc979f126`). Docker
Dependabot is in the `all-dependencies` group.

The generated stub requires `grpcio>=1.85.3` and `protobuf>=7.35.1`.
`protobuf` is in the extra because the generated module imports it.
The HTTP install does not.

Uvicorn `timeout_graceful_shutdown` is 30 seconds. The lifespan only
yields. It does not cancel a handler.

`requirements.txt` is not updated by the uv Dependabot group. The
local CI diff is the check.

## Suggested next work

PyPI publish stays open (`SERVE-001-T2`). The example image stays
unpublished.

## Recent history

- feat(ingress): cap bodies before buffering and serve generated Run
- ci: hash-lock the image and pin the quality workflows
- docs: record 0.2.0
- release: tag v0.2.0

*Last updated: 2026-11-26.*
