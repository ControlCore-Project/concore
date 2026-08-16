# [Wire Format](@id wire-format)

```@meta
DocTestSetup = :(using Main.Concore)
```

Concore messages are text lists containing a simulation timestamp followed by
zero or more data values:

```text
[simtime, value1, value2, ...]
```

For example:

```text
[5.0, 1.5, -2.0]
```

The first value is the timestamp. `concore_read` updates `Concore.simtime` and
returns only `[1.5, -2.0]` to the node.

## Writing

For vector writes, the outgoing timestamp is `Concore.simtime + delta`:

```julia
Concore.simtime = 5.0
concore_write(1, "u", [1.5, -2.0]; delta=1)
```

This writes:

```text
[6.0, 1.5, -2.0]
```

Integer-valued finite floats are written with a `.0` suffix. Other values are
rounded to 15 significant digits to keep output consistent with the existing
Concore wire format.

## Reading

`safe_parse_list` parses wire values without calling `eval` or `Meta.parse`.
For compatibility with Python and NumPy output, it also accepts wrapped values
and Python literals:

```jldoctest
julia> safe_parse_list("[0.0, np.float64(1.5), True, None]") == [0.0, 1.5, 1.0, 0.0]
true
```

Malformed input raises `ArgumentError`. The protocol, wire compatibility, and
interop tests cover Julia exchanges with the existing Python, C++, MATLAB, and
Verilog implementations.
