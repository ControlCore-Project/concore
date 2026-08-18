# Concore.jl

Concore.jl is the native Julia implementation of the Concore protocol. It uses
the same wire format and synchronization pattern as the existing Concore
runtimes, without calling through Python.

The runtime is the standalone file `concore.jl`. Julia nodes keep it next to
their source and include it directly:

```julia
include("concore.jl")
using .Concore
```

File transport is the default. Memory-mapped files and ZeroMQ are available as
optional backend selections, and `concoredocker.jl` provides the path defaults
used by generated Docker studies.

## Contents

- [Getting Started](@ref getting-started) covers setup, the standard node loop, and configuration.
- [API Reference](@ref api-reference) lists the public Julia interface.
- [Backends](@ref backends) describes File, Mmap, ZMQ, and Docker usage.
- [Wire Format](@ref wire-format) documents message encoding and simulation time.
