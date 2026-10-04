# Development S3 emulator, built from official sources rather than removed images.
FROM golang:1.26-alpine AS builder
RUN apk add --no-cache ca-certificates git
ENV CGO_ENABLED=0 GOBIN=/out GOMAXPROCS=2 GOFLAGS=-p=2
RUN --mount=type=cache,target=/go/pkg/mod --mount=type=cache,target=/root/.cache/go-build \
    go install github.com/minio/minio@v0.0.0-20260212201848-7aac2a2c5b7c
RUN --mount=type=cache,target=/go/pkg/mod --mount=type=cache,target=/root/.cache/go-build \
    go install github.com/minio/mc@v0.0.0-20251106162529-77f82e18b540

FROM alpine:3.23 AS runtime
RUN apk add --no-cache ca-certificates && addgroup -g 10001 storage && adduser -D -u 10001 -G storage storage

FROM runtime AS server
COPY --from=builder /out/minio /usr/local/bin/minio
RUN mkdir /data && chown storage:storage /data
USER storage
EXPOSE 9000 9001
ENTRYPOINT ["minio"]
CMD ["server", "/data", "--console-address", ":9001"]

FROM runtime AS client
COPY --from=builder /out/mc /usr/local/bin/mc
USER storage
ENTRYPOINT ["mc"]
