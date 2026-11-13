# Benchmark results

These results were measured on August 3, 2026 at commit `2024bd3`.

## Environment

| Item | Value |
|---|---|
| CPU | AMD Ryzen 5 4600H, 6 cores / 12 threads |
| OS | Windows 11 Home Single Language, build 26200, 64-bit |
| Julia | 1.10.11 |
| Python | 3.11.4 |
| ZMQ.jl | 1.5.1 |

## Method

Both scripts used the wire value `[0.0, 1.0, 2.0, 3.0, 4.0]`. A round trip
writes a request, reads it, writes a reply, and reads the reply through the
current Concore API.

Each full run used 5,000 iterations, 100 warmup operations, and five measured
repetitions. Julia and Python were run alternately three times each. The tables
report the median of the three run-level medians. Setup and Julia compilation
were outside the timed sections. Ratios were calculated from the median batch
times before the displayed rates were rounded.

ZMQ.jl 1.5.1 was installed in the temporary Julia project used for these
runs. No repository dependency files were changed. The commands were run from
the repository root:

```powershell
julia +1.10 --startup-file=no --project=$env:TEMP\concore-benchmark-julia-1.10 benchmark\bench_julia.jl
py -3.11 benchmark\bench_python.py
```

## Julia backends

Batch time covers 5,000 round trips. The range shows the rates from the three
complete runs.

| Backend | Median batch (ms) | Round trips/s | Run range |
|---|---:|---:|---:|
| File | 21,208.055 | 236 | 211-238 |
| Mmap | 2,839.998 | 1,761 | 1,744-1,791 |
| ZMQ | 1,174.931 | 4,256 | 4,218-4,264 |

On this machine, the observed Mmap rate was 7.47 times the File rate and the
ZMQ rate was 18.05 times the File rate.

## Julia and Python

Batch time covers 5,000 operations or round trips. The ratio is the Julia rate
divided by the Python rate.

| Workload | Julia batch (ms) | Python batch (ms) | Julia rate | Python rate | Ratio |
|---|---:|---:|---:|---:|---:|
| Parse wire | 17.905 | 57.348 | 279,250 ops/s | 87,187 ops/s | 3.20 |
| Format wire | 3.343 | 3.852 | 1,495,663 ops/s | 1,297,926 ops/s | 1.15 |
| File round trip | 21,208.055 | 22,247.748 | 236 round trips/s | 225 round trips/s | 1.05 |

The parse result showed the largest difference in the matched workloads. File
round-trip rates were close, and the Julia File result varied more across the
three runs than the Mmap and ZMQ results.

## Implementation notes

The matched workloads use the current parser and formatter behavior and the
current File APIs in each language. The Julia implementation is native and
does not call through Python. Julia also exposes File, Mmap, and ZMQ through
the same read/write API; the Mmap and ZMQ numbers above are Julia backend
comparisons, not cross-language comparisons.

## Limitations

- Results come from one Windows machine and may change with the filesystem
  cache, power settings, and background activity.
- The ZMQ benchmark uses two local sockets in one process. It does not include
  network or process scheduling overhead.
- The round-trip workload is sequential and does not model a full study.
- Julia and Python overlap only on parse, format, and File round trips in this
  suite.
- These measurements are not CI thresholds or general performance guarantees.
