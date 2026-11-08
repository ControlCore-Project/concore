import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.channels.FileLock;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.List;

/**
 * Java implementation of concore local communication.
 *
 * This class provides file-based inter-process communication for control systems,
 * mirroring the functionality of concore.py.
 */
public class concore {
    private static final ConcoreJavaRuntimeCore runtime = new ConcoreJavaRuntimeCore("./in", "./out", true);

    private static final Path BASE_DIR = Paths.get("").toAbsolutePath().normalize();
    private static final Path PID_REGISTRY_FILE = BASE_DIR.resolve("concorekill_pids.txt");
    private static final Path KILL_SCRIPT_FILE = BASE_DIR.resolve("concorekill.bat");

    // initialize on class load, same as Python module-level init
    static {
        if (isWindows()) {
            registerPid();
            writeKillScript();
            Runtime.getRuntime().addShutdownHook(new Thread(concore::cleanupPid));
        }
        Runtime.getRuntime().addShutdownHook(new Thread(concore::terminateZmq));
    }

    private static boolean isWindows() {
        String os = System.getProperty("os.name");
        return os != null && os.toLowerCase().contains("win");
    }

    private static void registerPid() {
        try {
            ProcessHandle current = ProcessHandle.current();
            long pid = current.pid();
            long startTimeMs = current.info().startInstant()
                    .orElseThrow(() -> new IllegalStateException(
                            "Process start time is unavailable"))
                    .toEpochMilli();
            String record = pid + "|" + startTimeMs + System.lineSeparator();
            try (FileChannel channel = FileChannel.open(PID_REGISTRY_FILE,
                    StandardOpenOption.CREATE, StandardOpenOption.WRITE,
                    StandardOpenOption.APPEND)) {
                try (FileLock lock = channel.lock()) {
                    ByteBuffer buffer = ByteBuffer.wrap(
                            record.getBytes(java.nio.charset.StandardCharsets.UTF_8));
                    while (buffer.hasRemaining()) {
                        channel.write(buffer);
                    }
                }
            }
        } catch (IOException | RuntimeException e) {
        }
    }
    private static void cleanupPid() {
        String pid = String.valueOf(ProcessHandle.current().pid());
        if (!Files.exists(PID_REGISTRY_FILE)) return;
        try (FileChannel channel = FileChannel.open(PID_REGISTRY_FILE,
                StandardOpenOption.READ, StandardOpenOption.WRITE)) {
            try (FileLock lock = channel.lock()) {
                ByteBuffer buf = ByteBuffer.allocate((int) channel.size());
                while (buf.hasRemaining() && channel.read(buf) != -1) {
                }
                buf.flip();
                String content = java.nio.charset.StandardCharsets.UTF_8
                        .decode(buf).toString();
                List<String> remaining = new ArrayList<>();
                for (String line : content.split("\\R")) {
                    String trimmed = line.trim();
                    if (!trimmed.isEmpty()) {
                        String entryPid = trimmed.split("\\|", 2)[0].trim();
                        if (!entryPid.equals(pid)) {
                            remaining.add(trimmed);
                        }
                    }
                }
                StringBuilder sb = new StringBuilder();
                for (String entry : remaining) {
                    sb.append(entry).append(System.lineSeparator());
                }
                channel.truncate(0);
                channel.position(0);
                ByteBuffer output = ByteBuffer.wrap(
                        sb.toString().getBytes(
                                java.nio.charset.StandardCharsets.UTF_8));
                while (output.hasRemaining()) {
                    channel.write(output);
                }
            }
        } catch (IOException e) {
        }
    }
    private static void writeKillScript() {
        try {
            String helperName = "concorekill.ps1";
            String script =
                    "@echo off\r\n" +
                    "setlocal\r\n" +
                    "if not exist \"%~dp0" + helperName + "\" (\r\n" +
                    "    echo Missing process cleanup helper: \"%~dp0"
                            + helperName + "\"\r\n" +
                    "    exit /b 1\r\n" +
                    ")\r\n" +
                    "powershell.exe -NoLogo -NoProfile -NonInteractive "
                            + "-ExecutionPolicy Bypass -File \"%~dp0"
                            + helperName + "\"\r\n" +
                    "exit /b %ERRORLEVEL%\r\n";
            Files.write(KILL_SCRIPT_FILE,
                    script.getBytes(java.nio.charset.StandardCharsets.UTF_8));
        } catch (IOException e) {
        }
    }
    /**
     * Sets maxtime from concore.maxtime file, or uses defaultValue if file not found.
     * Catches both IOException and RuntimeException to match Python safe_literal_eval.
     */
    public static void defaultMaxTime(double defaultValue) {
        runtime.defaultMaxTime(defaultValue);
    }

    // package-level helpers for testing with temp directories
    static void setInPath(String path) { runtime.setInPath(path); }
    static void setOutPath(String path) { runtime.setOutPath(path); }
    static void setDelay(int ms) { runtime.setDelay(ms); }
    static double getSimtime() { return runtime.getSimtime(); }
    static void resetState() { runtime.resetState(); }

    public static boolean unchanged() {
        return runtime.unchanged();
    }

    public static Object tryParam(String n, Object i) {
        return runtime.tryParam(n, i);
    }

    /**
     * Reads data from a port file. Returns the values after extracting simtime.
     * Input format: [simtime, val1, val2, ...]
     * Returns: list of values after simtime
     * Includes max retry limit to avoid infinite blocking (matches Python behavior).
     */
    public static ReadResult read(int port, String name, String initstr) {
        return convertResult(runtime.readFilePort(port, name, initstr));
    }

    /**
     * Writes data to a port file.
     * Prepends simtime+delta to the value list, then serializes to Python-literal format.
     * Accepts List or String values (matching Python implementation).
     */
    public static void write(int port, String name, Object val, int delta) {
        runtime.writeFilePort(port, name, val, delta);
    }

    /**
     * Parses an initial value string like "[0.0, 1.0, 2.0]".
     * Extracts simtime from position 0 and returns the remaining values as a List.
     */
    public static List<Object> initVal(String simtimeVal) {
        return runtime.initVal(simtimeVal);
    }

    public static void initZmqPort(String portName, String portType, String address, String socketTypeStr) {
        runtime.initZmqPort(portName, portType, address, socketTypeStr);
    }

    public static void terminateZmq() {
        runtime.terminateZmq();
    }

    /**
     * Reads data from a ZMQ port. Same wire format as file-based read:
     * expects [simtime, val1, val2, ...], strips simtime, returns the rest.
     */
    public static ReadResult read(String portName, String name, String initstr) {
        return convertResult(runtime.readZmqPort(portName, name, initstr));
    }

    /**
     * Writes data to a ZMQ port. Prepends [simtime+delta] to match file-based write behavior.
     */
    public static void write(String portName, String name, Object val, int delta) {
        runtime.writeZmqPort(portName, name, val, delta);
    }

    /**
     * Parses a Python-literal string into Java objects using a recursive descent parser.
     * Supports: dict, list, int, float, string (single/double quoted), bool, None, nested structures.
     * This replaces the broken split-based parser that could not handle quoted commas or nesting.
     */
    static Object literalEval(String s) {
        return ConcoreJavaRuntimeCore.literalEval(s);
    }

    private static ReadStatus convertStatus(ConcoreJavaRuntimeCore.ReadStatus status) {
        return ReadStatus.valueOf(status.name());
    }

    private static ReadResult convertResult(ConcoreJavaRuntimeCore.ReadResult result) {
        return new ReadResult(convertStatus(result.status), result.data);
    }

    public enum ReadStatus {
        SUCCESS, FILE_NOT_FOUND, TIMEOUT, PARSE_ERROR, RETRIES_EXCEEDED
    }

    public static class ReadResult {
        public final ReadStatus status;
        public final List<Object> data;
        ReadResult(ReadStatus status, List<Object> data) {
            this.status = status;
            this.data = data;
        }
    }

}
