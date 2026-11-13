# [Getting Started](@id getting-started)

```@meta
DocTestSetup = :(using Main.Concore)
```

## Setup

Concore.jl requires Julia 1.10 or later. Clone the Concore repository and run
Julia from the repository root:

```sh
git clone https://github.com/ControlCore-Project/concore.git
cd concore
julia
```

Load the standalone runtime from a Julia node:

```julia
include("concore.jl")
using .Concore
```

There are no required Julia package dependencies for the default File backend.
ZMQ.jl is only needed when using the ZMQ backend.

## Node loop

A Concore node reads until its input changes, performs its calculation, and
writes its output. This controller reads `ym` from input port 1 and writes `u`
to output port 1:

```julia
include("concore.jl")
using .Concore

Concore.default_maxtime!(100)
Concore.delay = 0.02

ym = initval("[0.0, 0.0]")

while Concore.simtime < Concore.maxtime
    while unchanged()
        ym = concore_read(1, "ym", "[0.0, 0.0]")
    end

    u = 1.01 .* ym
    concore_write(1, "u", u; delta=0)
end
```

With the default paths, port 1 reads from `./in1/ym` and writes to
`./out1/u`. The study runner creates and connects those directories.

The repository also contains a mixed Python and Julia file-backend demo:

```sh
julia demo/run_julia_mixed_demo.jl
```

## Initial values and simulation time

`initval` parses a wire value and sets `Concore.simtime` from its first value:

```jldoctest
julia> ym = initval("[0.0, 1.5]"); (Concore.simtime, ym)
(0.0, [1.5])
```

`ym` is `[1.5]` and `Concore.simtime` is `0.0`. A read returns only the data
values and updates simulation time to the largest timestamp seen. A write uses
`Concore.simtime + delta` as the outgoing timestamp.

## Configuration

The runtime loads the same files as the other Concore implementations:

- `concore.iport` maps named input ports to numbers.
- `concore.oport` maps named output ports to numbers.
- `concore.params` supplies values returned by `tryparam`.
- `concore.maxtime` sets the simulation limit used by `default_maxtime!`.

Parameters can use Python dictionary syntax or semicolon-separated key/value
pairs:

```text
{'gain': 1.5, 'mode': 'auto'}
```

```text
gain=1.5;mode=auto
```

Use a default when a parameter is absent:

```julia
gain = tryparam("gain", 1.0)
```
