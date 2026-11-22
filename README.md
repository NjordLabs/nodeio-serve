# nodeio-serve

HTTP and gRPC ingress for one request handler. The handler is the
caller's function. This package does not import
[nodeio](https://github.com/NjordLabs/nodeio). Point the handler at a
nodeio graph when that is what should run.

The package is not on PyPI. Install the release tag:

```bash
pip install "nodeio-serve @ git+https://github.com/NjordLabs/nodeio-serve.git@v0.1.0"
```

Requires Python 3.13.

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
`proto/nodeio/v1/graph.proto`. `GraphServicer.run` takes the request
body as bytes and returns JSON bytes. It is not a generated stub.

The container image is an example. It is not published. Build it from
this repository:

```bash
docker build -t nodeio-serve:local .
docker run --rm --read-only --cap-drop ALL \
  --security-opt no-new-privileges \
  -p 127.0.0.1:8080:8080 nodeio-serve:local
```

There is no `HEALTHCHECK` in the image. Use `GET /health`. The process
listens on `127.0.0.1` unless `NODEIO_SERVE_HOST` is set. The example
image sets that variable to `0.0.0.0` so the process is reachable on
the container network. Publish the port on `127.0.0.1`.

Source and issues:
[NjordLabs/nodeio-serve](https://github.com/NjordLabs/nodeio-serve)
