# concore.jl -- Standalone single-file Concore module (file-based, relative paths)
#
# This file is a self-contained version of the Concore.jl package for use
# with mkconcore.py.  It is copied into each node directory and included via:
#
#     include("concore.jl")
#     using .Concore
#
# Uses relative paths (./in, ./out) for local execution.
# For Docker containers, use concoredocker.jl instead.
#
# No external dependencies -- only Julia stdlib.

module Concore

using Mmap

# -----------------------------------------------------------------------------
# Backend selection
# -----------------------------------------------------------------------------

"""Abstract supertype for concore communication backends."""
abstract type AbstractBackend end

"""Default local file transport backend."""
struct FileBackend <: AbstractBackend end

"""Memory-mapped local file transport backend."""
struct MmapBackend <: AbstractBackend
    segment_size::Int

    function MmapBackend(segment_size::Int = 4096)
        segment_size > 1 || throw(ArgumentError("mmap segment size must be greater than 1"))
        new(segment_size)
    end
end

# Compatibility name for proposal/docs wording.
const FileTransport = FileBackend
const MmapTransport = MmapBackend

# -----------------------------------------------------------------------------
# Path configuration
# -----------------------------------------------------------------------------

const _INPATH  = "./in"
const _OUTPATH = "./out"

# -----------------------------------------------------------------------------
# Module-level globals (Python API compatibility)
# -----------------------------------------------------------------------------

"""Accumulated read data for sync detection."""
global s::String = ""

"""Previous accumulated data for sync comparison."""
global olds::String = ""

"""Sleep interval between polling reads in seconds."""
global delay::Float64 = 1.0

"""Cumulative file-read retry count (diagnostic)."""
global retrycount::Int = 0

"""Current simulation time."""
global simtime::Float64 = 0.0

"""Maximum simulation time."""
global maxtime::Float64 = 100.0

"""Input port name -> number mapping."""
global iport::Dict{String,Int} = Dict{String,Int}()

"""Output port name -> number mapping."""
global oport::Dict{String,Int} = Dict{String,Int}()

"""Runtime parameters loaded from concore.params."""
global params::Dict{String,Any} = Dict{String,Any}()

"""Active communication backend."""
global _backend::AbstractBackend = FileBackend()

"""Input path prefix."""
global inpath::String = _INPATH

"""Output path prefix."""
global outpath::String = _OUTPATH

# Maximum accumulated `s` string length to prevent unbounded growth.
const _S_MAX_LEN = 65_536

# -----------------------------------------------------------------------------
# Internal helpers
# -----------------------------------------------------------------------------

_backend_inpath(::FileBackend) = inpath
_backend_outpath(::FileBackend) = outpath
_backend_inpath(::MmapBackend) = inpath
_backend_outpath(::MmapBackend) = outpath

_input_dir(port::Int) = _backend_inpath(_backend) * string(port)
_output_dir(port::Int) = _backend_outpath(_backend) * string(port)

const _mmap_segments = Dict{String, Tuple{IOStream, Vector{UInt8}}}()
const _mmap_cleanup_registered = Ref(false)

function _register_mmap_cleanup()
    if !_mmap_cleanup_registered[]
        atexit(mmap_cleanup)
        _mmap_cleanup_registered[] = true
    end
end

function _close_mmap_segment(path::AbstractString)
    segment = pop!(_mmap_segments, String(path), nothing)
    segment === nothing && return nothing

    io, buf = segment
    try
        Mmap.sync!(buf)
    catch
    end
    try
        finalize(buf)
    catch
    end
    try
        isopen(io) && close(io)
    catch
    end
    GC.gc()
    return nothing
end

function _mmap_segment(path::AbstractString, size::Int)::Vector{UInt8}
    segment = get(_mmap_segments, String(path), nothing)
    if segment !== nothing && isopen(segment[1]) && length(segment[2]) >= size
        return segment[2]
    end
    if segment !== nothing
        _close_mmap_segment(path)
    end

    _register_mmap_cleanup()
    mkpath(dirname(path))

    io = open(path, isfile(path) ? "r+" : "w+")
    if filesize(path) < size
        seek(io, size - 1)
        write(io, UInt8(0))
        seekstart(io)
    end

    buf = try
        Mmap.mmap(io, Vector{UInt8}, size)
    catch
        close(io)
        rethrow()
    end
    _mmap_segments[String(path)] = (io, buf)
    return buf
end

function _mmap_content(buf::Vector{UInt8})::String
    nullpos = findfirst(iszero, buf)
    last = nullpos === nothing ? length(buf) : nullpos - 1
    last <= 0 && return ""
    return String(copy(buf[1:last]))
end

function _mmap_read(path::AbstractString, initstr::AbstractString, size::Int)::String
    isfile(path) || return String(initstr)
    buf = _mmap_segment(path, size)
    ins = _mmap_content(buf)
    return isempty(ins) ? String(initstr) : ins
end

function _mmap_write(path::AbstractString, wire::AbstractString, size::Int)
    bytes = Vector{UInt8}(wire)
    if length(bytes) >= size
        throw(ArgumentError("mmap payload exceeds segment size"))
    end

    buf = _mmap_segment(path, size)
    n = length(bytes)
    buf[1:n] .= bytes
    buf[n + 1] = 0x00
    if n + 2 <= size
        buf[n + 2:size] .= 0x00
    end
    Mmap.sync!(buf)
    return nothing
end

function _write_wire_file(path::AbstractString, wire::AbstractString)
    segment = get(_mmap_segments, String(path), nothing)
    if segment !== nothing && isopen(segment[1])
        return _mmap_write(path, wire, length(segment[2]))
    end

    open(path, "w") do f
        write(f, wire)
    end
    return nothing
end

"""Close open memory-mapped segment handles."""
function mmap_cleanup()
    segments = collect(values(_mmap_segments))
    empty!(_mmap_segments)

    for (io, buf) in segments
        try
            Mmap.sync!(buf)
        catch
        end
        try
            finalize(buf)
        catch
        end
        try
            isopen(io) && close(io)
        catch
        end
    end

    segments = nothing
    GC.gc()
    return nothing
end

function _wire_content(raw::AbstractString)::String
    nullpos = findfirst(==('\0'), raw)
    nullpos === nothing && return String(raw)
    return String(raw[1:nullpos - 1])
end

function _port_file_path(base::AbstractString, port::Int, name::AbstractString)::String
    port_dir = abspath(base * string(port))
    filepath = abspath(joinpath(port_dir, String(name)))
    rel = relpath(filepath, port_dir)
    parts = splitpath(rel)
    if isabspath(rel) || (!isempty(parts) && parts[1] == "..")
        throw(ArgumentError("invalid file name '$name' for port $port"))
    end
    return filepath
end

"""Append `addition` to `current`, truncating from the front if too long."""
function _cap_s(current::AbstractString, addition::AbstractString)::String
    combined = current * addition
    len = length(combined)
    if len > _S_MAX_LEN
        return combined[end - _S_MAX_LEN + 1:end]
    end
    return combined
end

"""Format a Vector{Float64} as a concore wire-format string."""
function _format_wire(vals::Vector{Float64})::String
    buf = IOBuffer()
    print(buf, "[")
    for (i, v) in enumerate(vals)
        i > 1 && print(buf, ", ")
        if isinteger(v) && isfinite(v) && abs(v) < 1e15
            print(buf, string(Int(v)), ".0")
        else
            print(buf, round(v; sigdigits=15))
        end
    end
    print(buf, "]")
    return String(take!(buf))
end

# -----------------------------------------------------------------------------
# Wire-format parser
# -----------------------------------------------------------------------------

"""
    safe_parse_list(str::AbstractString) -> Vector{Float64}

Parse a concore wire-format string `[simtime, v1, v2, ...]` into a
`Vector{Float64}`.  Handles numpy wrappers and Python booleans.
Never calls `eval` or `Meta.parse`.
"""
function safe_parse_list(str::AbstractString)::Vector{Float64}
    cleaned = strip(str)

    if isempty(cleaned)
        throw(ArgumentError("safe_parse_list: input string is empty"))
    end

    # Strip outer numpy array wrapper: np.array([...]) -> [...]
    cleaned = replace(cleaned, r"^(?:np|numpy)\.array\(" => "")
    cleaned = replace(cleaned, r"\)$" => "")
    cleaned = strip(cleaned)

    # Strip individual numpy wrappers: np.float64(1.5) -> 1.5
    cleaned = replace(cleaned, r"(?:np|numpy)\.\w+\(([^()]+)\)" => s"\1")

    # Python booleans / None
    cleaned = replace(cleaned, r"\bTrue\b"  => "1.0")
    cleaned = replace(cleaned, r"\bFalse\b" => "0.0")
    cleaned = replace(cleaned, r"\bNone\b"  => "0.0")

    # Validate bracket structure
    m = match(r"^\[(.+)\]$", cleaned)
    if m === nothing
        throw(ArgumentError(
            "safe_parse_list: expected '[...]' format, got '$(first(str, 80))'"))
    end

    inner = m.captures[1]
    parts = split(inner, ",")

    result = Vector{Float64}(undef, length(parts))
    for (i, part) in enumerate(parts)
        token = strip(part)
        val = tryparse(Float64, token)
        if val === nothing
            throw(ArgumentError(
                "safe_parse_list: cannot parse '$(token)' as Float64 " *
                "(position $i in '$(first(str, 80))')"))
        end
        result[i] = val
    end

    return result
end

# -----------------------------------------------------------------------------
# Port / param config loading
# -----------------------------------------------------------------------------

"""Parse a concore port config file (Python dict syntax) -> Dict{String,Int}."""
function parse_port_file(filename::AbstractString)::Dict{String,Int}
    result = Dict{String,Int}()
    isfile(filename) || return result

    content = try
        strip(read(filename, String))
    catch
        return result
    end

    isempty(content) && return result

    # Strip outer braces
    content = replace(content, r"^\{" => "")
    content = replace(content, r"\}$" => "")

    # Match 'key': value pairs
    for m in eachmatch(r"['\"]([^'\"]+)['\"]\s*:\s*(-?\d+)", content)
        result[m.captures[1]] = parse(Int, m.captures[2])
    end

    return result
end

"""Load input port configuration from `concore.iport`."""
function load_iport!()
    global iport
    iport = parse_port_file("concore.iport")
    return iport
end

"""Load output port configuration from `concore.oport`."""
function load_oport!()
    global oport
    oport = parse_port_file("concore.oport")
    return oport
end

"""
    load_params!()

Load runtime parameters from `{inpath}1/concore.params`.
Supports Python dict format and key=value;key2=value2 format.
"""
function load_params!()
    global params
    params_path = joinpath(_input_dir(1), "concore.params")
    isfile(params_path) || return

    sparams = try
        strip(read(params_path, String))
    catch
        return
    end

    isempty(sparams) && return

    # Strip surrounding double quotes (Windows path quoting artefact)
    if length(sparams) >= 2 && sparams[1] == '"' && sparams[end] == '"'
        sparams = sparams[2:end-1]
    end

    params = Dict{String,Any}()

    if startswith(sparams, "{")
        # Python dict format: {'key': value, ...}
        for m in eachmatch(r"['\"]([^'\"]+)['\"]\s*:\s*([^,}]+)", sparams)
            key = m.captures[1]
            val_str = strip(m.captures[2])
            val = tryparse(Float64, val_str)
            params[key] = val !== nothing ? val : strip(val_str, ['\'', '"'])
        end
    else
        # key=value;key2=value2 format
        for pair in split(sparams, ";")
            kv = split(strip(pair), "="; limit=2)
            length(kv) == 2 || continue
            key = strip(kv[1])
            val_str = strip(kv[2])
            val = tryparse(Float64, val_str)
            params[key] = val !== nothing ? val : val_str
        end
    end
end

"""Return parameter `name` from `params`, or `default` if not found."""
tryparam(name::AbstractString, default) = get(params, name, default)

"""
    default_maxtime!(default::Int) -> Int

Read maximum simulation time from `{inpath}1/concore.maxtime`, or use `default`.
"""
function default_maxtime!(default::Real)
    global maxtime
    maxtime_path = joinpath(_input_dir(1), "concore.maxtime")
    maxtime = try
        parse(Float64, strip(read(maxtime_path, String)))
    catch
        Float64(default)
    end
    return maxtime
end

# -----------------------------------------------------------------------------
# Core protocol: read / write / unchanged / initval
# -----------------------------------------------------------------------------

"""
    concore_read(port::Int, name::AbstractString, initstr::AbstractString) -> Vector{Float64}

Read data from input port file `{inpath}{port}/{name}`.
Implements the concore polling protocol with retry on empty reads.
Returns data values (without simtime).
"""
function concore_read(
    port::Int,
    name::AbstractString,
    initstr::AbstractString,
)::Vector{Float64}
    global s, simtime, retrycount

    sleep(delay)

    filepath = _port_file_path(_backend_inpath(_backend), port, name)

    ins = ""
    try
        if _backend isa MmapBackend
            ins = _mmap_read(filepath, initstr, _backend.segment_size)
        else
            ins = _wire_content(read(filepath, String))
        end
    catch
        ins = initstr
    end

    # Retry if file was empty (writer may not have flushed yet)
    attempts = 0
    while isempty(ins) && attempts < 5
        sleep(delay)
        try
            if _backend isa MmapBackend
                ins = _mmap_read(filepath, initstr, _backend.segment_size)
            else
                ins = _wire_content(read(filepath, String))
            end
        catch
        end
        attempts += 1
        retrycount += 1
    end

    if isempty(ins)
        ins = initstr
    end

    # Accumulate for sync detection, capped to prevent unbounded growth
    s = _cap_s(s, ins)

    val = safe_parse_list(ins)
    simtime = max(simtime, val[1])
    return val[2:end]
end

"""
    concore_write(port::Int, name::AbstractString, val::AbstractVector{<:Real}; delta::Real=0)

Write data to output port file `{outpath}{port}/{name}`.
Wire format: `[simtime+delta, val1, val2, ...]`.
"""
function concore_write(
    port::Int,
    name::AbstractString,
    val::AbstractVector{<:Real};
    delta::Real = 0,
)
    filepath = _port_file_path(_backend_outpath(_backend), port, name)
    mkpath(dirname(filepath))

    outval = Float64[simtime + Float64(delta); Float64.(val)]
    wire = _format_wire(outval)

    if _backend isa MmapBackend
        _mmap_write(filepath, wire, _backend.segment_size)
    else
        _write_wire_file(filepath, wire)
    end

    return nothing
end

"""
    concore_write(port::Int, name::AbstractString, val::AbstractString; delta::Int=0)

Write a raw string to the output port file.
"""
function concore_write(
    port::Int,
    name::AbstractString,
    val::AbstractString;
    delta::Int = 0,
)
    sleep(2 * delay)
    filepath = _port_file_path(_backend_outpath(_backend), port, name)
    mkpath(dirname(filepath))
    if _backend isa MmapBackend
        _mmap_write(filepath, val, _backend.segment_size)
    else
        _write_wire_file(filepath, val)
    end
    return nothing
end

"""
    initval(simtime_val::AbstractString) -> Vector{Float64}

Parse initial value string, set simtime, return data portion.
"""
function initval(simtime_val::AbstractString)::Vector{Float64}
    global simtime
    val = safe_parse_list(simtime_val)
    simtime = val[1]
    return val[2:end]
end

"""
    unchanged() -> Bool

Return `true` if no new data has been read since the last call.
Standard sync loop: `while unchanged(); ym = concore_read(...); end`
"""
function unchanged()::Bool
    global s, olds
    if olds == s
        s = ""
        return true
    else
        olds = s
        return false
    end
end

# -----------------------------------------------------------------------------
# Initialization
# -----------------------------------------------------------------------------

"""
    concore_init!()

Initialize by loading port configs, parameters, and maxtime from filesystem.
"""
function concore_init!()
    load_iport!()
    load_oport!()
    load_params!()
    default_maxtime!(100)
    return nothing
end

function concore_init!(backend::AbstractBackend)
    global _backend
    _backend = backend
    concore_init!()
    return nothing
end

# Backward-compatible aliases (without !)
const load_iport = load_iport!
const load_oport = load_oport!
const load_params = load_params!
const default_maxtime = default_maxtime!
const concore_init = concore_init!

# -----------------------------------------------------------------------------
# Exports
# -----------------------------------------------------------------------------

export concore_read, concore_write, initval, unchanged
export tryparam, default_maxtime!, safe_parse_list
export load_iport!, load_oport!, load_params!, concore_init!
export load_iport, load_oport, load_params, default_maxtime, concore_init
export AbstractBackend, FileBackend, FileTransport
export MmapBackend, MmapTransport, mmap_cleanup

# -----------------------------------------------------------------------------
# Auto-initialize on load
# -----------------------------------------------------------------------------

function __init__()
    try
        concore_init!()
    catch
        # Expected when config files don't exist yet
    end
end

end # module Concore
