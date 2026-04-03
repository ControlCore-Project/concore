FROM ubuntu:20.04

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        iverilog && rm -rf /var/lib/apt/lists/*

COPY . /src
WORKDIR /src

