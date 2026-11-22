# nodeio-serve

HTTP and gRPC ingress for a [nodeio](https://github.com/NjordLabs/nodeio)
graph. The caller passes the function that runs one request. This image
is an example and is not published.

```bash
pip install nodeio-serve
```

`GET /health` returns `{"status": "ok"}`. `POST /v1/run` accepts one
JSON object, rejects a body over the cap, and runs at most the
configured number of requests at once.

The gRPC contract is `nodeio.v1.GraphService/Run` in
`proto/nodeio/v1/graph.proto`.

```bash
docker build -t nodeio-serve:local .
```

Run the example read-only, with capabilities dropped:

```bash
docker run --rm --read-only --cap-drop ALL --security-opt no-new-privileges \
  -p 127.0.0.1:8080:8080 nodeio-serve:local
```

There is no `HEALTHCHECK` in the image. The caller uses `GET /health`.
The process listens on `127.0.0.1` unless `NODEIO_SERVE_HOST` is set.
The example image sets that variable to `0.0.0.0` so the process is
reachable inside the container network namespace. Publish the port on
`127.0.0.1`.
