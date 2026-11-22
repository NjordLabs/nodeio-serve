# syntax=docker/dockerfile:1
# python:3.13-slim-bookworm

FROM python:3.15-slim-bookworm@sha256:96599df822d0e1c6bb700014a05c7f3c8cabc6e0f7ff3c4f9f69cee033b4b5d9 AS build

WORKDIR /build
COPY requirements.txt ./
COPY src ./src
# Dependencies are hash-locked. The package itself is copied into
# site-packages so the image does not pip-install it without hashes.
# The slim base has no setuptools, and a build isolation download
# would be unpinned.
RUN pip install --no-cache-dir --require-hashes -r requirements.txt \
    && python -c "import pathlib, shutil, sysconfig; root = pathlib.Path(sysconfig.get_path('purelib')); shutil.copytree('src/nodeio_serve', root / 'nodeio_serve')"

FROM python:3.15-slim-bookworm@sha256:96599df822d0e1c6bb700014a05c7f3c8cabc6e0f7ff3c4f9f69cee033b4b5d9

LABEL org.opencontainers.image.title="nodeio-serve" \
      org.opencontainers.image.description="HTTP and gRPC ingress for a nodeio graph" \
      org.opencontainers.image.source="https://github.com/NjordLabs/nodeio-serve" \
      org.opencontainers.image.version="0.2.0" \
      org.opencontainers.image.revision="unknown" \
      org.opencontainers.image.licenses="MIT"

COPY --from=build /usr/local /usr/local
ENV NODEIO_SERVE_HOST=0.0.0.0
USER 65532:65532
EXPOSE 8080
ENTRYPOINT ["python", "-m", "nodeio_serve"]
