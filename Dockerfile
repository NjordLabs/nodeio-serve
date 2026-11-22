# syntax=docker/dockerfile:1

FROM python:3.13-slim-bookworm@sha256:a5a7017efc5969e00ae2b91c8eb0631049a569652aa4ffc4501769049ae45c72 AS build

WORKDIR /build
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .

FROM python:3.13-slim-bookworm@sha256:a5a7017efc5969e00ae2b91c8eb0631049a569652aa4ffc4501769049ae45c72

LABEL org.opencontainers.image.title="nodeio-serve" \
      org.opencontainers.image.description="HTTP and gRPC ingress for a nodeio graph" \
      org.opencontainers.image.source="https://github.com/NjordLabs/nodeio-serve"

COPY --from=build /usr/local /usr/local
ENV NODEIO_SERVE_HOST=0.0.0.0
USER 65532:65532
EXPOSE 8080
ENTRYPOINT ["python", "-m", "nodeio_serve"]
