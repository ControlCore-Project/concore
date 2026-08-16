# [Backends](@id backends)

The active backend controls how `concore_read` and `concore_write` move the
same wire-format strings. File is the default backend.

## File

`FileBackend` uses ordinary files and has no external Julia dependencies.

```julia
include("concore.jl")
using .Concore

concore_init!(FileBackend())
```

Local input and output path prefixes are `./in` and `./out`. The numeric port
is appended to the prefix, so port 1 uses `./in1` and `./out1`.

## Mmap

`MmapBackend` keeps the file-based naming and wire format but accesses each
file through a fixed-size memory-mapped segment. The default segment size is
4096 bytes.

```julia
concore_init!(MmapBackend())

try
    value = concore_read(1, "ym", "[0.0, 0.0]")
    concore_write(1, "u", value)
finally
    mmap_cleanup()
end
```

Pass a different segment size when constructing the backend if the wire value
does not fit in the default segment:

```julia
concore_init!(MmapBackend(8192))
```

## [ZMQ](@id zmq)

ZMQ support is optional. Install ZMQ.jl in the active Julia environment before
including `concore.jl`:

```julia
using Pkg
Pkg.add("ZMQ")
```

`Concore.HAS_ZMQ` reports whether the package was available when the runtime
was loaded. ZMQ ports use string names instead of numeric file ports. This
example shows the request side of a REQ/REP pair:

```julia
include("concore.jl")
using .Concore

concore_init!(ZmqBackend())
init_zmq_port("req", "connect", "tcp://127.0.0.1:5555", "REQ")

try
    concore_write("req", "u", [1.0])
    ym = concore_read("req", "ym", "[0.0, 0.0]")
finally
    terminate_zmq()
end
```

A REP peer must bind the same address and receive before replying.

## Docker

Docker is a runtime path variant, not a separate backend type.
`concoredocker.jl` uses `/in` and `/out` as its path prefixes, producing paths
such as `/in1/ym` and `/out1/u`.

For generated Docker studies, `mkconcore.py` copies `concoredocker.jl` into the
node build directory as `concore.jl`. The node source therefore keeps the same
include statement used locally:

```julia
include("concore.jl")
using .Concore
```

Build the mixed Julia controller and Python plant example with the existing
study generator:

```sh
concore build demo/sampleJ.graphml --source demo --output docker-julia-demo --type docker --compose
cd docker-julia-demo
./build
./maxtime 5
docker compose up
```

The generated Compose file mounts the connected input and output directories
at the paths expected by each container.
