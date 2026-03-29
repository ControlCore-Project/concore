# Java end-to-end example

This example runs a Python controller (`controller.py`) and a Java PM node (`pm_java.java`) over the standard concore file-based exchange.

## Files

- `controller.py` - Python controller node
- `pm_java.java` - Java PM node using `concoredocker.java`
- `java_e2e.graphml` - workflow graph for the example
- `smoke_check.py` - lightweight verification script

## Prerequisites

- Python environment with project dependencies installed
- JDK (for `javac` and `java`)
- `jeromq-0.6.0.jar`

Download jar (from repo root):

```bash
mkdir -p .ci-cache/java
curl -fsSL -o .ci-cache/java/jeromq-0.6.0.jar https://repo1.maven.org/maven2/org/zeromq/jeromq/0.6.0/jeromq-0.6.0.jar
```

## Run smoke check

From repo root:

```bash
python example/java_e2e/smoke_check.py --jar .ci-cache/java/jeromq-0.6.0.jar
```

Expected result:

- script prints `smoke_check passed`
- final `u` and `ym` payloads are printed in concore wire format
