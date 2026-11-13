# [API Reference](@id api-reference)

```@meta
CurrentModule = Concore
```

## Protocol

```@docs
concore_read
concore_write
initval
unchanged
```

## Configuration

```@docs
safe_parse_list
tryparam
default_maxtime!
load_iport!
load_oport!
load_params!
concore_init!
```

The compatibility names `default_maxtime`, `load_iport`, `load_oport`,
`load_params`, and `concore_init` are aliases for the corresponding functions
above.

`FileTransport`, `MmapTransport`, and `ZmqTransport` are aliases for the
corresponding backend types.

## Backends

```@docs
AbstractBackend
FileBackend
MmapBackend
mmap_cleanup
ZmqBackend
```

ZMQ ports are registered with
`init_zmq_port(name, mode, address, socket_type)` and closed with
`terminate_zmq()`. These functions require the optional ZMQ.jl package. See
[ZMQ](@ref zmq) for a complete call sequence.
