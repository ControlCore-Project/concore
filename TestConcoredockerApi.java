import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.*;

/**
 * Tests for concoredocker read(), write(), unchanged(), initVal()
 * using temp directories for file-based IPC.
 */
public class TestConcoredockerApi {
    static int passed = 0;
    static int failed = 0;

    public static void main(String[] args) {
        // zero delay so tests don't sleep for 1s per read()
        concoredocker.setDelay(0);

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
            return Files.createTempDirectory("concore_test_");
        } catch (IOException e) {
            throw new RuntimeException("Failed to create temp dir", e);
        }
    }

    /** Creates temp dir with port subdirectory ready for write(). */
    static Path makeTempDir(int port) {
        Path tmp = makeTempDir();
        try {
            Files.createDirectories(tmp.resolve(String.valueOf(port)));
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
        return tmp;
    }

    static void writeFile(Path base, int port, String name, String content) {
        try {
            Path dir = base.resolve(String.valueOf(port));
            Files.createDirectories(dir);
            Files.write(dir.resolve(name), content.getBytes());
        } catch (IOException e) {
            throw new RuntimeException("Failed to write test file", e);
        }
    }

    static String readFile(Path base, int port, String name) {
        try {
            return new String(Files.readAllBytes(base.resolve(String.valueOf(port)).resolve(name)));
        } catch (IOException e) {
            throw new RuntimeException("Failed to read test file", e);
        }
    }

    static void testWriteProducesCorrectFormat() {
        Path tmp = makeTempDir(1);
        concoredocker.resetState();
        concoredocker.setOutPath(tmp.toString());

        List<Object> vals = new ArrayList<>();
        vals.add(10.0);
        vals.add(20.0);
        concoredocker.write(1, "signal", vals, 1);

        String content = readFile(tmp, 1, "signal");
        @SuppressWarnings("unchecked")
        List<Object> parsed = (List<Object>) concoredocker.literalEval(content);
        check("write: simtime+delta as first element", 1.0, parsed.get(0));
        check("write: val1 correct", 10.0, parsed.get(1));
        check("write: val2 correct", 20.0, parsed.get(2));
    }

    static void testReadParsesFileAndStripsSimtime() {
        Path tmp = makeTempDir();
        concoredocker.resetState();
        concoredocker.setInPath(tmp.toString());
        writeFile(tmp, 1, "sensor", "[0.0, 42.0, 99.0]");

        concoredocker.ReadResult result = concoredocker.read(1, "sensor", "[0.0, 0.0, 0.0]");
        check("read: status SUCCESS", concoredocker.ReadStatus.SUCCESS, result.status);
        check("read: strips simtime, size=2", 2, result.data.size());
        check("read: val1 correct", 42.0, result.data.get(0));
        check("read: val2 correct", 99.0, result.data.get(1));
    }

    static void testReadWriteRoundtrip() {
        Path tmp = makeTempDir(1);
        concoredocker.resetState();
        concoredocker.setInPath(tmp.toString());
        concoredocker.setOutPath(tmp.toString());

        List<Object> outVals = new ArrayList<>();
        outVals.add(7.0);
        outVals.add(8.0);
        concoredocker.write(1, "data", outVals, 1);

        concoredocker.ReadResult inVals = concoredocker.read(1, "data", "[0.0, 0.0, 0.0]");
        check("roundtrip: status", concoredocker.ReadStatus.SUCCESS, inVals.status);
        check("roundtrip: size", 2, inVals.data.size());
        check("roundtrip: val1", 7.0, inVals.data.get(0));
        check("roundtrip: val2", 8.0, inVals.data.get(1));
    }

    static void testSimtimeAdvancesWithDelta() {
        Path tmp = makeTempDir(1);
        concoredocker.resetState();
        concoredocker.setInPath(tmp.toString());
        concoredocker.setOutPath(tmp.toString());

        List<Object> v = Collections.singletonList((Object) 1.0);

        // iteration 1: simtime=0, delta=1 -> file has [1.0, 1.0], read -> simtime becomes 1.0
        concoredocker.write(1, "tick", v, 1);
        concoredocker.read(1, "tick", "[0.0, 0.0]");
        check("simtime after iter 1", 1.0, concoredocker.getSimtime());

        // iteration 2: write again with delta=1 -> file has [2.0, 1.0], read -> simtime becomes 2.0
        concoredocker.write(1, "tick", v, 1);
        concoredocker.read(1, "tick", "[0.0, 0.0]");
        check("simtime after iter 2", 2.0, concoredocker.getSimtime());
    }

    static void testUnchangedReturnsFalseAfterRead() {
        Path tmp = makeTempDir();
        concoredocker.resetState();
        concoredocker.setInPath(tmp.toString());
        writeFile(tmp, 1, "sig", "[0.0, 5.0]");

        concoredocker.read(1, "sig", "[0.0, 0.0]");
        check("unchanged: false right after read", false, concoredocker.unchanged());
    }

    static void testUnchangedReturnsTrueOnSameData() {
        Path tmp = makeTempDir();
        concoredocker.resetState();
        concoredocker.setInPath(tmp.toString());
        writeFile(tmp, 1, "sig", "[0.0, 5.0]");

        concoredocker.read(1, "sig", "[0.0, 0.0]");
        concoredocker.unchanged(); // first call: false, locks olds = s
        check("unchanged: true on second call with same data", true, concoredocker.unchanged());
    }

    static void testInitValExtractsSimtime() {
        concoredocker.resetState();
        concoredocker.initVal("[2.0, 10, 20]");
        check("initVal: simtime extracted", 2.0, concoredocker.getSimtime());
    }

    static void testInitValReturnsRemainingValues() {
        concoredocker.resetState();
        List<Object> result = concoredocker.initVal("[3.5, 100, 200]");
        check("initVal: size of returned list", 2, result.size());
        check("initVal: first remaining val", 100, result.get(0));
        check("initVal: second remaining val", 200, result.get(1));
    }

    static void testOutputFileMatchesPythonWireFormat() {
        Path tmp = makeTempDir(1);
        concoredocker.resetState();
        concoredocker.setOutPath(tmp.toString());

        List<Object> vals = new ArrayList<>();
        vals.add(1.0);
        vals.add(2.0);
        concoredocker.write(1, "out", vals, 0);

        String raw = readFile(tmp, 1, "out");
        check("wire format: starts with '['", true, raw.startsWith("["));
        check("wire format: ends with ']'", true, raw.endsWith("]"));
        Object reparsed = concoredocker.literalEval(raw);
        check("wire format: re-parseable as list", true, reparsed instanceof List);
    }

    static void testReadFileNotFound() {
        Path tmp = makeTempDir();
        concoredocker.resetState();
        concoredocker.setInPath(tmp.toString());
        // no file written, port 1/missing does not exist
        concoredocker.ReadResult result = concoredocker.read(1, "missing", "[0.0, 0.0]");
        check("read file not found: status", concoredocker.ReadStatus.FILE_NOT_FOUND, result.status);
        check("read file not found: data is default", 1, result.data.size());
    }

    static void testReadRetriesExceeded() {
        Path tmp = makeTempDir();
        concoredocker.resetState();
        concoredocker.setInPath(tmp.toString());
        writeFile(tmp, 1, "empty", ""); // always empty, exhausts retries
        concoredocker.ReadResult result = concoredocker.read(1, "empty", "[0.0, 0.0]");
        check("read retries exceeded: status", concoredocker.ReadStatus.RETRIES_EXCEEDED, result.status);
        check("read retries exceeded: data is default", 1, result.data.size());
    }

    static void testReadParseError() {
        Path tmp = makeTempDir();
        concoredocker.resetState();
        concoredocker.setInPath(tmp.toString());
        writeFile(tmp, 1, "bad", "not_a_valid_list");
        concoredocker.ReadResult result = concoredocker.read(1, "bad", "[0.0, 0.0]");
        check("read parse error: status", concoredocker.ReadStatus.PARSE_ERROR, result.status);
        check("read parse error: data is default", 1, result.data.size());
    }

    static void testReadTraversalBlocked() {
        Path tmp = makeTempDir();
        concoredocker.resetState();
        concoredocker.setInPath(tmp.toString());

        concoredocker.ReadResult result = concoredocker.read(1, "../escape", "[0.0, 7.0]");
        check("read traversal blocked: status", concoredocker.ReadStatus.PARSE_ERROR, result.status);
        check("read traversal blocked: returns default", 1, result.data.size());
    }

    static void testWriteTraversalBlocked() {
        Path tmp = makeTempDir(1);
        concoredocker.resetState();
        concoredocker.setOutPath(tmp.toString());

        concoredocker.write(1, "../escape", Collections.singletonList((Object) 1.0), 0);
        check("write traversal blocked: no escaped file", false, Files.exists(tmp.resolve("escape")));
    }
}
