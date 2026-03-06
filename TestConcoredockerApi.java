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

        List<Object> result = concoredocker.read(1, "sensor", "[0.0, 0.0, 0.0]");
        check("read: strips simtime, size=2", 2, result.size());
        check("read: val1 correct", 42.0, result.get(0));
        check("read: val2 correct", 99.0, result.get(1));
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

        List<Object> inVals = concoredocker.read(1, "data", "[0.0, 0.0, 0.0]");
        check("roundtrip: size", 2, inVals.size());
        check("roundtrip: val1", 7.0, inVals.get(0));
        check("roundtrip: val2", 8.0, inVals.get(1));
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
}
