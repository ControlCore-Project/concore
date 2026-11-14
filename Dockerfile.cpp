FROM ubuntu:22.04

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        g++ && rm -rf /var/lib/apt/lists/*

COPY . /src
WORKDIR /src

