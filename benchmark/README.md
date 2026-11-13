# Concore benchmarks

The benchmark scripts compare Julia's File, Mmap, and ZMQ backends and run
matched Julia and Python workloads.

Measured results and analysis are in [RESULTS.md](RESULTS.md).

Run the full benchmarks from the repository root:

```sh
julia --startup-file=no benchmark/bench_julia.jl
python benchmark/bench_python.py
```

Use `--quick` for a smoke run:

```sh
julia --startup-file=no benchmark/bench_julia.jl --quick
python benchmark/bench_python.py --quick
```

The scripts use the wire value `[0.0, 1.0, 2.0, 3.0, 4.0]`. The parse and
format workloads use the current language runtime behavior. A round trip
writes a request, reads it, writes a reply, and reads the reply through the
current Concore API.

The normal run uses 5,000 iterations, 100 warmup operations, and five measured
repetitions. Quick mode uses 100 iterations, 10 warmup operations, and three
measured repetitions. Setup and warmup are outside the timed sections. Output
reports the median batch time and the rate calculated from that median.

File and Mmap use a temporary directory. ZMQ uses a local REQ/REP socket pair
and is skipped when ZMQ.jl is unavailable. The Julia/Python comparison covers
the matched parse, format, and File round-trip workloads.

Results depend on the host, filesystem cache, and runtime versions. The ZMQ
measurement uses two sockets in one process and does not include network or
process scheduling overhead. These scripts are not intended as CI performance
thresholds.
