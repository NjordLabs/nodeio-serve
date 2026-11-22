# AI agent handoff

## Identity

`nodeio-serve` is the HTTP and gRPC ingress. Python 3.13. Public
repository `NjordLabs/nodeio-serve`. The image is an example and is
not published.

## Scope

`GET /health`, `POST /v1/run`, and `nodeio.v1.GraphService/Run`. The
handler is injected. The engine stays in nodeio.

## Commands

```bash
sh scripts/check-ci-local.sh
docker build -t nodeio-serve:local .
```

## Known pitfalls

Quality jobs pull a private `ci-lint` image and stay red until
`GHCR_READ_TOKEN` can read it. The container workflow sets
`push_handoff: false` and `scan_local: true`.

## Suggested next work

Point the injected handler at a nodeio `run` once nodeio is released.

## Recent history

- feat(ingress): add HTTP and gRPC run endpoints

*Last updated: 2026-11-22.*
