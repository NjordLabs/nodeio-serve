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

`v0.1.0` is released. The container workflow sets
`push_handoff: false` and `scan_local: true`. The example image is
not published.

## Suggested next work

PyPI publish stays open. nodeio `v0.2.0` is released. The example
image stays unpublished.

## Recent history

- feat(ingress): add HTTP and gRPC run endpoints
- fix(quality): decode JSON behind a stub and cover the echo entrypoint
- docs(readme): install from the v0.1.0 git tag

*Last updated: 2026-11-22.*
