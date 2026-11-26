# nodeio-serve

HTTP and gRPC ingress for one request handler. The handler is the
caller's function. This package does not import
[nodeio](https://github.com/NjordLabs/nodeio). Point the handler at a
nodeio graph when that is what should run.

The package is not on PyPI. Install the wheel from the GitHub Release:

```bash
pip install https://github.com/NjordLabs/nodeio-serve/releases/download/v0.3.0/nodeio_serve-0.3.0-py3-none-any.whl
```

Requires Python 3.13 or 3.14.

```python
from nodeio_serve import create_app


async def echo(payload: dict[str, object]) -> dict[str, object]:
    return payload


app = create_app(echo)
```

`GET /health` returns `{"status": "ok"}`. `POST /v1/run` accepts one
JSON object, rejects a body over the cap, and runs at most the
configured number of requests at once.

The gRPC method is `nodeio.v1.GraphService/Run`, defined in
`proto/nodeio/v1/graph.proto`. The servicer is generated. It needs the
`grpc` extra (`grpcio` and `protobuf`). The default install and the
example image do not include it.

```python
from nodeio_serve import create_ingress

app, servicer = create_ingress(echo)
```

`create_ingress` returns the HTTP application and the servicer. They
share one concurrency limit and the same body cap.

The container image is an example. It is not published. Build it from
this repository:

```bash
docker build -t nodeio-serve:local .
docker run --rm --read-only --cap-drop ALL \
  --security-opt no-new-privileges \
  --tmpfs /tmp:rw,noexec,nosuid,size=64m \
  -p 127.0.0.1:8080:8080 nodeio-serve:local
```

The image does not authenticate callers. There is no `HEALTHCHECK`.
Use `GET /health`. The process listens on `127.0.0.1` unless
`NODEIO_SERVE_HOST` is set. The example image sets that variable to
`0.0.0.0` so the process is reachable on the container network.
Publish the port on `127.0.0.1`.

Source and issues:
[NjordLabs/nodeio-serve](https://github.com/NjordLabs/nodeio-serve)
