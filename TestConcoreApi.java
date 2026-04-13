import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.*;

/**
 * Tests for concore read(), write(), unchanged(), initVal()
 * using temp directories for file-based IPC.
 */
public class TestConcoreApi {
    static int passed = 0;
    static int failed = 0;

    public static void main(String[] args) {
        concore.setDelay(0);

        testWriteProducesCorrectFormat();
        testReadParsesFileAndStripsSimtime();
        testReadWriteRoundtrip();
        testSimtimeAdvancesWithDelta();
        testUnchangedReturnsFalseAfterRead();
        testUnchangedReturnsTrueOnSameData();
        testInitValExtractsSimtime();
        testInitValReturnsRemainingValues();
        testOutputFileMatchesPythonWireFormat();
        testReadFileNotFound();
        testReadRetriesExceeded();
        testReadParseError();
        testReadTraversalBlocked();
        testWriteTraversalBlocked();

        System.out.println("\n=== Results: " + passed + " passed, " + failed + " failed out of " + (passed + failed) + " tests ===");
        if (failed > 0) {
            System.exit(1);
        }
    }

    static void check(String testName, Object expected, Object actual) {
        if (Objects.equals(expected, actual)) {
            System.out.println("PASS: " + testName);
            passed++;
        } else {
            System.out.println("FAIL: " + testName + " | expected: " + expected + " | actual: " + actual);
            failed++;
        }
    }

    static Path makeTempDir() {
        try {
            return Files.createTempDirectory("concore_local_test_");
        } catch (IOException e) {
            throw new RuntimeException("Failed to create temp dir", e);
        }
    }

    static String basePath(Path tmp) {
        return tmp.resolve("in").toString();
    }

    static Path portDir(String base, int port) {
        return Paths.get(base + port);
    }

    static void writeFile(String base, int port, String name, String content) {
        try {
            Path dir = portDir(base, port);
            Files.createDirectories(dir);
            Files.write(dir.resolve(name), content.getBytes());
        } catch (IOException e) {
            throw new RuntimeException("Failed to write test file", e);
        }
    }

    static String readFile(String base, int port, String name) {
        try {
            return new String(Files.readAllBytes(portDir(base, port).resolve(name)));
        } catch (IOException e) {
            throw new RuntimeException("Failed to read test file", e);
        }
    }

    static void testWriteProducesCorrectFormat() {
        Path tmp = makeTempDir();
        String base = basePath(tmp);
        concore.resetState();
        concore.setOutPath(base);
        try {
            Files.createDirectories(portDir(base, 1));
        } catch (IOException e) {
            throw new RuntimeException(e);
        }

        List<Object> vals = new ArrayList<>();
        vals.add(10.0);
        vals.add(20.0);
        concore.write(1, "signal", vals, 1);

        String content = readFile(base, 1, "signal");
        @SuppressWarnings("unchecked")
        List<Object> parsed = (List<Object>) concore.literalEval(content);
        check("write: simtime+delta as first element", 1.0, parsed.get(0));
        check("write: val1 correct", 10.0, parsed.get(1));
        check("write: val2 correct", 20.0, parsed.get(2));
    }

    static void testReadParsesFileAndStripsSimtime() {
        Path tmp = makeTempDir();
        String base = basePath(tmp);
        concore.resetState();
        concore.setInPath(base);
        writeFile(base, 1, "sensor", "[0.0, 42.0, 99.0]");

        concore.ReadResult result = concore.read(1, "sensor", "[0.0, 0.0, 0.0]");
        check("read: status SUCCESS", concore.ReadStatus.SUCCESS, result.status);
        check("read: strips simtime, size=2", 2, result.data.size());
        check("read: val1 correct", 42.0, result.data.get(0));
        check("read: val2 correct", 99.0, result.data.get(1));
    }

    static void testReadWriteRoundtrip() {
        Path tmp = makeTempDir();
        String base = basePath(tmp);
        concore.resetState();
        concore.setInPath(base);
        concore.setOutPath(base);
        try {
            Files.createDirectories(portDir(base, 1));
        } catch (IOException e) {
            throw new RuntimeException(e);
        }

        List<Object> outVals = new ArrayList<>();
        outVals.add(7.0);
        outVals.add(8.0);
        concore.write(1, "data", outVals, 1);

        concore.ReadResult inVals = concore.read(1, "data", "[0.0, 0.0, 0.0]");
        check("roundtrip: status", concore.ReadStatus.SUCCESS, inVals.status);
        check("roundtrip: size", 2, inVals.data.size());
        check("roundtrip: val1", 7.0, inVals.data.get(0));
        check("roundtrip: val2", 8.0, inVals.data.get(1));
    }

    static void testSimtimeAdvancesWithDelta() {
        Path tmp = makeTempDir();
        String base = basePath(tmp);
        concore.resetState();
        concore.setInPath(base);
        concore.setOutPath(base);
        try {
            Files.createDirectories(portDir(base, 1));
        } catch (IOException e) {
            throw new RuntimeException(e);
        }

        List<Object> v = Collections.singletonList((Object) 1.0);

        concore.write(1, "tick", v, 1);
        concore.read(1, "tick", "[0.0, 0.0]");
        check("simtime after iter 1", 1.0, concore.getSimtime());

        concore.write(1, "tick", v, 1);
        concore.read(1, "tick", "[0.0, 0.0]");
        check("simtime after iter 2", 2.0, concore.getSimtime());
    }

    static void testUnchangedReturnsFalseAfterRead() {
        Path tmp = makeTempDir();
        String base = basePath(tmp);
        concore.resetState();
        concore.setInPath(base);
        writeFile(base, 1, "sig", "[0.0, 5.0]");

        concore.read(1, "sig", "[0.0, 0.0]");
        check("unchanged: false right after read", false, concore.unchanged());
    }

    static void testUnchangedReturnsTrueOnSameData() {
        Path tmp = makeTempDir();
        String base = basePath(tmp);
        concore.resetState();
        concore.setInPath(base);
        writeFile(base, 1, "sig", "[0.0, 5.0]");

        concore.read(1, "sig", "[0.0, 0.0]");
        concore.unchanged();
        check("unchanged: true on second call with same data", true, concore.unchanged());
    }

    static void testInitValExtractsSimtime() {
        concore.resetState();
        concore.initVal("[2.0, 10, 20]");
        check("initVal: simtime extracted", 2.0, concore.getSimtime());
    }

    static void testInitValReturnsRemainingValues() {
        concore.resetState();
        List<Object> result = concore.initVal("[3.5, 100, 200]");
        check("initVal: size of returned list", 2, result.size());
        check("initVal: first remaining val", 100, result.get(0));
        check("initVal: second remaining val", 200, result.get(1));
    }

    static void testOutputFileMatchesPythonWireFormat() {
        Path tmp = makeTempDir();
        String base = basePath(tmp);
        concore.resetState();
        concore.setOutPath(base);
        try {
            Files.createDirectories(portDir(base, 1));
        } catch (IOException e) {
            throw new RuntimeException(e);
        }

        List<Object> vals = new ArrayList<>();
        vals.add(1.0);
        vals.add(2.0);
        concore.write(1, "out", vals, 0);

        String raw = readFile(base, 1, "out");
        check("wire format: starts with '['", true, raw.startsWith("["));
        check("wire format: ends with ']'", true, raw.endsWith("]"));
        Object reparsed = concore.literalEval(raw);
        check("wire format: re-parseable as list", true, reparsed instanceof List);
    }

    static void testReadFileNotFound() {
        Path tmp = makeTempDir();
        String base = basePath(tmp);
        concore.resetState();
        concore.setInPath(base);
        concore.ReadResult result = concore.read(1, "missing", "[0.0, 0.0]");
        check("read file not found: status", concore.ReadStatus.FILE_NOT_FOUND, result.status);
        check("read file not found: data is default", 1, result.data.size());
    }

    static void testReadRetriesExceeded() {
        Path tmp = makeTempDir();
        String base = basePath(tmp);
        concore.resetState();
        concore.setInPath(base);
        writeFile(base, 1, "empty", "");
        concore.ReadResult result = concore.read(1, "empty", "[0.0, 0.0]");
        check("read retries exceeded: status", concore.ReadStatus.RETRIES_EXCEEDED, result.status);
        check("read retries exceeded: data is default", 1, result.data.size());
    }

    static void testReadParseError() {
        Path tmp = makeTempDir();
        String base = basePath(tmp);
        concore.resetState();
        concore.setInPath(base);
        writeFile(base, 1, "bad", "not_a_valid_list");
        concore.ReadResult result = concore.read(1, "bad", "[0.0, 0.0]");
        check("read parse error: status", concore.ReadStatus.PARSE_ERROR, result.status);
        check("read parse error: data is default", 1, result.data.size());
    }

    static void testReadTraversalBlocked() {
        Path tmp = makeTempDir();
        String base = basePath(tmp);
        concore.resetState();
        concore.setInPath(base);

        concore.ReadResult result = concore.read(1, "../escape", "[0.0, 7.0]");
        check("read traversal blocked: status", concore.ReadStatus.PARSE_ERROR, result.status);
        check("read traversal blocked: returns default", 1, result.data.size());
    }

    static void testWriteTraversalBlocked() {
        Path tmp = makeTempDir();
        String base = basePath(tmp);
        concore.resetState();
        concore.setOutPath(base);
        try {
            Files.createDirectories(portDir(base, 1));
        } catch (IOException e) {
            throw new RuntimeException(e);
        }

        concore.write(1, "../escape", Collections.singletonList((Object) 1.0), 0);
        check("write traversal blocked: no escaped file", false, Files.exists(tmp.resolve("escape")));
    }
}
