import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.channels.FileLock;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardOpenOption;
import java.util.HashMap;
import java.util.Map;
import java.util.ArrayList;
import java.util.List;
import org.zeromq.ZMQ;

/**
 * Java implementation of concore local communication.
 *
 * This class provides file-based inter-process communication for control systems,
 * mirroring the functionality of concore.py.
 */
public class concore {
    private static Map<String, Object> iport = new HashMap<>();
    private static Map<String, Object> oport = new HashMap<>();
    private static String s = "";
    private static String olds = "";
    // delay in milliseconds (Python uses time.sleep(1) = 1 second)
    private static int delay = 1000;
    private static int retrycount = 0;
    private static int maxRetries = 5;
    private static String inpath = "./in";
    private static String outpath = "./out";
    private static Map<String, Object> params = new HashMap<>();
    private static Map<String, ZeroMQPort> zmqPorts = new HashMap<>();
    private static ZMQ.Context zmqContext = null;
    // simtime as double to preserve fractional values (e.g. "[0.0, ...]")
    private static double simtime = 0;
    private static double maxtime;

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
        try {
            iport = parseFile("concore.iport");
        } catch (IOException e) {
        }
        try {
            oport = parseFile("concore.oport");
        } catch (IOException e) {
        }
        try {
            String paramsFile = Paths.get(portPath(inpath, 1), "concore.params").toString();
            String sparams = new String(Files.readAllBytes(Paths.get(paramsFile)), java.nio.charset.StandardCharsets.UTF_8);
            if (sparams.length() > 0 && sparams.charAt(0) == '"') { // windows keeps "" need to remove
                sparams = sparams.substring(1);
                sparams = sparams.substring(0, sparams.indexOf('"'));
            }
            params = parseParams(sparams);
        } catch (IOException e) {
            params = new HashMap<>();
        }
        defaultMaxTime(100);
        Runtime.getRuntime().addShutdownHook(new Thread(concore::terminateZmq));
    }

    private static boolean isWindows() {
        String os = System.getProperty("os.name");
        return os != null && os.toLowerCase().contains("win");
    }

    private static void registerPid() {
        try {
            String pid = String.valueOf(ProcessHandle.current().pid());
            try (FileChannel channel = FileChannel.open(PID_REGISTRY_FILE,
                    StandardOpenOption.CREATE, StandardOpenOption.WRITE, StandardOpenOption.APPEND)) {
                try (FileLock lock = channel.lock()) {
                    channel.write(ByteBuffer.wrap((pid + System.lineSeparator()).getBytes(java.nio.charset.StandardCharsets.UTF_8)));
                }
            }
        } catch (IOException e) {
        }
    }

    private static void cleanupPid() {
        String pid = String.valueOf(ProcessHandle.current().pid());
        if (!Files.exists(PID_REGISTRY_FILE)) return;
        List<String> remaining = new ArrayList<>();
        try (FileChannel channel = FileChannel.open(PID_REGISTRY_FILE,
                StandardOpenOption.READ, StandardOpenOption.WRITE)) {
            try (FileLock lock = channel.lock()) {
                ByteBuffer buf = ByteBuffer.allocate((int) channel.size());
                channel.read(buf);
                buf.flip();
                String content = java.nio.charset.StandardCharsets.UTF_8.decode(buf).toString();
                for (String line : content.split("\\R")) {
                    String trimmed = line.trim();
                    if (!trimmed.isEmpty() && !trimmed.equals(pid)) {
                        remaining.add(trimmed);
                    }
                }
                channel.truncate(0);
                channel.position(0);
                if (!remaining.isEmpty()) {
                    StringBuilder sb = new StringBuilder();
                    for (String r : remaining) sb.append(r).append(System.lineSeparator());
                    channel.write(ByteBuffer.wrap(sb.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8)));
                }
            }
        } catch (IOException e) {
        }
        if (remaining.isEmpty()) {
            try { Files.deleteIfExists(PID_REGISTRY_FILE); } catch (IOException e) {}
            try { Files.deleteIfExists(KILL_SCRIPT_FILE); } catch (IOException e) {}
        }
    }

    private static void writeKillScript() {
        try {
            String regName = PID_REGISTRY_FILE.getFileName().toString();
            String batName = KILL_SCRIPT_FILE.getFileName().toString();
            String script = "@echo off\r\n";
            script += "if not exist \"%~dp0" + regName + "\" (\r\n";
            script += "    echo No PID registry found. Nothing to kill.\r\n";
            script += "    exit /b 0\r\n";
            script += ")\r\n";
            script += "for /f \"usebackq tokens=*\" %%p in (\"%~dp0" + regName + "\") do (\r\n";
            script += "    wmic process where \"ProcessId=%%p\" get CommandLine /value 2>nul | find /i \"concore\" >nul\r\n";
            script += "    if not errorlevel 1 (\r\n";
            script += "        echo Killing concore process %%p\r\n";
            script += "        taskkill /F /PID %%p >nul 2>&1\r\n";
            script += "    ) else (\r\n";
            script += "        echo Skipping PID %%p - not a concore process or not running\r\n";
            script += "    )\r\n";
            script += ")\r\n";
            script += "del /q \"%~dp0" + regName + "\" 2>nul\r\n";
            script += "del /q \"%~dp0" + batName + "\" 2>nul\r\n";
            Files.write(KILL_SCRIPT_FILE, script.getBytes(java.nio.charset.StandardCharsets.UTF_8));
        } catch (IOException e) {
        }
    }

    /**
     * Parses a param string into a map, matching concore_base.parse_params.
     * Tries dict literal first, then falls back to semicolon-separated key=value pairs.
     */
    private static Map<String, Object> parseParams(String sparams) {
        Map<String, Object> result = new HashMap<>();
        if (sparams == null || sparams.isEmpty()) return result;
        String trimmed = sparams.trim();
        if (trimmed.startsWith("{") && trimmed.endsWith("}")) {
            try {
                Object val = literalEval(trimmed);
                if (val instanceof Map) {
                    @SuppressWarnings("unchecked")
                    Map<String, Object> map = (Map<String, Object>) val;
                    return map;
                }
            } catch (Exception e) {
            }
        }
        for (String item : trimmed.split(";")) {
            if (item.contains("=")) {
                String[] parts = item.split("=", 2); // split on first '=' only
                String key = parts[0].trim();
                String value = parts[1].trim();
                try {
                    result.put(key, literalEval(value));
                } catch (Exception e) {
                    result.put(key, value);
                }
            }
        }
        return result;
    }

    /**
     * Parses a file containing a Python-style dictionary literal.
     * Returns empty map if file is empty or malformed (matches Python safe_literal_eval).
     */
    private static Map<String, Object> parseFile(String filename) throws IOException {
        String content = new String(Files.readAllBytes(Paths.get(filename)), java.nio.charset.StandardCharsets.UTF_8);
        content = content.trim();
        if (content.isEmpty()) {
            return new HashMap<>();
        }
        try {
            Object result = literalEval(content);
            if (result instanceof Map) {
                @SuppressWarnings("unchecked")
                Map<String, Object> map = (Map<String, Object>) result;
                return map;
            }
        } catch (IllegalArgumentException e) {
            System.err.println("Failed to parse file as map: " + filename + " (" + e.getMessage() + ")");
        }
        return new HashMap<>();
    }

    /**
     * Sets maxtime from concore.maxtime file, or uses defaultValue if file not found.
     * Catches both IOException and RuntimeException to match Python safe_literal_eval.
     */
    public static void defaultMaxTime(double defaultValue) {
        try {
            String maxtimeFile = Paths.get(portPath(inpath, 1), "concore.maxtime").toString();
            String content = new String(Files.readAllBytes(Paths.get(maxtimeFile)));
            Object parsed = literalEval(content.trim());
            if (parsed instanceof Number) {
                maxtime = ((Number) parsed).doubleValue();
            } else {
                maxtime = defaultValue;
            }
        } catch (IOException | RuntimeException e) {
            maxtime = defaultValue;
        }
    }

    private static String portPath(String base, int portNum) {
        return base + portNum;
    }

    // package-level helpers for testing with temp directories
    static void setInPath(String path) { inpath = path; }
    static void setOutPath(String path) { outpath = path; }
    static void setDelay(int ms) { delay = ms; }
    static double getSimtime() { return simtime; }
    static void resetState() { s = ""; olds = ""; simtime = 0; }

    public static boolean unchanged() {
        if (olds.equals(s)) {
            s = "";
            return true;
        }
        olds = s;
        return false;
    }

    public static Object tryParam(String n, Object i) {
        if (params.containsKey(n)) {
            return params.get(n);
        } else {
            return i;
        }
    }

    /**
     * Reads data from a port file. Returns the values after extracting simtime.
     * Input format: [simtime, val1, val2, ...]
     * Returns: list of values after simtime
     * Includes max retry limit to avoid infinite blocking (matches Python behavior).
     */
    public static ReadResult read(int port, String name, String initstr) {
        // Parse default value upfront for consistent return type
        List<Object> defaultVal = new ArrayList<>();
        try {
            List<?> parsed = (List<?>) literalEval(initstr);
            if (parsed.size() > 1) {
                defaultVal = new ArrayList<>(parsed.subList(1, parsed.size()));
            }
        } catch (Exception e) {
            // initstr not parseable as list; defaultVal stays empty
        }

        String filePath = Paths.get(portPath(inpath, port), name).toString();
        try {
            Thread.sleep(delay);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            s += initstr;
            return new ReadResult(ReadStatus.TIMEOUT, defaultVal);
        }

        String ins;
        try {
            ins = new String(Files.readAllBytes(Paths.get(filePath)));
        } catch (IOException e) {
            System.out.println("File " + filePath + " not found, using default value.");
            s += initstr;
            return new ReadResult(ReadStatus.FILE_NOT_FOUND, defaultVal);
        }

        int attempts = 0;
        while (ins.length() == 0 && attempts < maxRetries) {
            try {
                Thread.sleep(delay);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                s += initstr;
                return new ReadResult(ReadStatus.TIMEOUT, defaultVal);
            }
            try {
                ins = new String(Files.readAllBytes(Paths.get(filePath)));
            } catch (IOException e) {
                System.out.println("Retry " + (attempts + 1) + ": Error reading " + filePath);
            }
            attempts++;
            retrycount++;
        }

        if (ins.length() == 0) {
            System.out.println("Max retries reached for " + filePath + ", using default value.");
            return new ReadResult(ReadStatus.RETRIES_EXCEEDED, defaultVal);
        }

        s += ins;
        try {
            List<?> inval = (List<?>) literalEval(ins);
            if (!inval.isEmpty()) {
                double firstSimtime = ((Number) inval.get(0)).doubleValue();
                simtime = Math.max(simtime, firstSimtime);
                return new ReadResult(ReadStatus.SUCCESS, new ArrayList<>(inval.subList(1, inval.size())));
            }
        } catch (Exception e) {
            System.out.println("Error parsing " + ins + ": " + e.getMessage());
        }
        return new ReadResult(ReadStatus.PARSE_ERROR, defaultVal);
    }

    /**
     * Escapes a Java string so it can be safely used as a single-quoted Python string literal.
     * At minimum, escapes backslash, single quote, newline, carriage return, and tab.
     */
    private static String escapePythonString(String s) {
        StringBuilder sb = new StringBuilder(s.length());
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            switch (c) {
                case '\\': sb.append("\\\\"); break;
                case '\'': sb.append("\\'"); break;
                case '\n': sb.append("\\n"); break;
                case '\r': sb.append("\\r"); break;
                case '\t': sb.append("\\t"); break;
                default: sb.append(c); break;
            }
        }
        return sb.toString();
    }

    /**
     * Converts a Java object to its Python-literal string representation.
     * True/False/None instead of true/false/null; strings single-quoted.
     */
    private static String toPythonLiteral(Object obj) {
        if (obj == null) return "None";
        if (obj instanceof Boolean) return ((Boolean) obj) ? "True" : "False";
        if (obj instanceof String) return "'" + escapePythonString((String) obj) + "'";
        if (obj instanceof Number) return obj.toString();
        if (obj instanceof List) {
            List<?> list = (List<?>) obj;
            StringBuilder sb = new StringBuilder("[");
            for (int i = 0; i < list.size(); i++) {
                if (i > 0) sb.append(", ");
                sb.append(toPythonLiteral(list.get(i)));
            }
            sb.append("]");
            return sb.toString();
        }
        if (obj instanceof Map) {
            Map<?, ?> map = (Map<?, ?>) obj;
            StringBuilder sb = new StringBuilder("{");
            boolean first = true;
            for (Map.Entry<?, ?> entry : map.entrySet()) {
                if (!first) sb.append(", ");
                sb.append(toPythonLiteral(entry.getKey())).append(": ").append(toPythonLiteral(entry.getValue()));
                first = false;
            }
            sb.append("}");
            return sb.toString();
        }
        return obj.toString();
    }

    /**
     * Escapes a Java string so it can be safely embedded in a JSON double-quoted string.
     * Escapes backslash, double quote, newline, carriage return, and tab.
     */
    private static String escapeJsonString(String s) {
        StringBuilder sb = new StringBuilder(s.length());
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            switch (c) {
                case '\\': sb.append("\\\\"); break;
                case '"':  sb.append("\\\""); break;
                case '\n': sb.append("\\n"); break;
                case '\r': sb.append("\\r"); break;
                case '\t': sb.append("\\t"); break;
                default: sb.append(c); break;
            }
        }
        return sb.toString();
    }

    /**
     * Converts a Java object to its JSON string representation.
     * true/false/null instead of True/False/None; strings double-quoted.
     */
    private static String toJsonLiteral(Object obj) {
        if (obj == null) return "null";
        if (obj instanceof Boolean) return ((Boolean) obj) ? "true" : "false";
        if (obj instanceof String) return "\"" + escapeJsonString((String) obj) + "\"";
        if (obj instanceof Number) return obj.toString();
        if (obj instanceof List) {
            List<?> list = (List<?>) obj;
            StringBuilder sb = new StringBuilder("[");
            for (int i = 0; i < list.size(); i++) {
                if (i > 0) sb.append(", ");
                sb.append(toJsonLiteral(list.get(i)));
            }
            sb.append("]");
            return sb.toString();
        }
        if (obj instanceof Map) {
            Map<?, ?> map = (Map<?, ?>) obj;
            StringBuilder sb = new StringBuilder("{");
            boolean first = true;
            for (Map.Entry<?, ?> entry : map.entrySet()) {
                if (!first) sb.append(", ");
                sb.append(toJsonLiteral(entry.getKey())).append(": ").append(toJsonLiteral(entry.getValue()));
                first = false;
            }
            sb.append("}");
            return sb.toString();
        }
        return obj.toString();
    }

    /**
     * Writes data to a port file.
     * Prepends simtime+delta to the value list, then serializes to Python-literal format.
     * Accepts List or String values (matching Python implementation).
     */
    public static void write(int port, String name, Object val, int delta) {
        try {
            String path = Paths.get(portPath(outpath, port), name).toString();
            StringBuilder content = new StringBuilder();
            if (val instanceof String) {
                Thread.sleep(2 * delay);
                content.append(val);
            } else if (val instanceof List) {
                List<?> listVal = (List<?>) val;
                content.append("[");
                content.append(toPythonLiteral(simtime + delta));
                for (int i = 0; i < listVal.size(); i++) {
                    content.append(", ");
                    content.append(toPythonLiteral(listVal.get(i)));
                }
                content.append("]");
                // simtime must not be mutated here.
                // Mutation breaks cross-language determinism.
            } else if (val instanceof Object[]) {
                // Legacy support for Object[] arguments
                Object[] arrayVal = (Object[]) val;
                content.append("[");
                content.append(toPythonLiteral(simtime + delta));
                for (Object o : arrayVal) {
                    content.append(", ");
                    content.append(toPythonLiteral(o));
                }
                content.append("]");
                // simtime must not be mutated here.
                // Mutation breaks cross-language determinism.
            } else {
                System.out.println("write must have list or str");
                return;
            }
            Files.write(Paths.get(path), content.toString().getBytes());
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            System.out.println("skipping " + outpath + "/" + port + "/" + name);
        } catch (IOException e) {
            System.out.println("skipping " + outpath + "/" + port + "/" + name);
        }
    }

    /**
     * Parses an initial value string like "[0.0, 1.0, 2.0]".
     * Extracts simtime from position 0 and returns the remaining values as a List.
     */
    public static List<Object> initVal(String simtimeVal) {
        List<Object> val = new ArrayList<>();
        try {
            List<?> inval = (List<?>) literalEval(simtimeVal);
            if (!inval.isEmpty()) {
                simtime = ((Number) inval.get(0)).doubleValue();
                val = new ArrayList<>(inval.subList(1, inval.size()));
            }
        } catch (Exception e) {
            System.out.println("Error parsing initVal: " + e.getMessage());
        }
        return val;
    }

    private static ZMQ.Context getZmqContext() {
        if (zmqContext == null) {
            zmqContext = ZMQ.context(1);
        }
        return zmqContext;
    }

    public static void initZmqPort(String portName, String portType, String address, String socketTypeStr) {
        if (zmqPorts.containsKey(portName)) return;
        int sockType = zmqSocketTypeFromString(socketTypeStr);
        if (sockType == -1) {
            System.err.println("initZmqPort: unknown socket type '" + socketTypeStr + "'");
            return;
        }
        zmqPorts.put(portName, new ZeroMQPort(portType, address, sockType));
    }

    public static void terminateZmq() {
        for (Map.Entry<String, ZeroMQPort> entry : zmqPorts.entrySet()) {
            entry.getValue().socket.close();
        }
        zmqPorts.clear();
        if (zmqContext != null) {
            zmqContext.term();
            zmqContext = null;
        }
    }

    private static int zmqSocketTypeFromString(String s) {
        switch (s.toUpperCase()) {
            case "REQ":  return ZMQ.REQ;
            case "REP":  return ZMQ.REP;
            case "PUB":  return ZMQ.PUB;
            case "SUB":  return ZMQ.SUB;
            case "PUSH": return ZMQ.PUSH;
            case "PULL": return ZMQ.PULL;
            case "PAIR": return ZMQ.PAIR;
            default:     return -1;
        }
    }

    /**
     * Reads data from a ZMQ port. Same wire format as file-based read:
     * expects [simtime, val1, val2, ...], strips simtime, returns the rest.
     */
    public static ReadResult read(String portName, String name, String initstr) {
        List<Object> defaultVal = new ArrayList<>();
        try {
            List<?> parsed = (List<?>) literalEval(initstr);
            if (parsed.size() > 1) {
                defaultVal = new ArrayList<>(parsed.subList(1, parsed.size()));
            }
        } catch (Exception e) {
        }
        ZeroMQPort port = zmqPorts.get(portName);
        if (port == null) {
            System.err.println("read: ZMQ port '" + portName + "' not initialized");
            return new ReadResult(ReadStatus.FILE_NOT_FOUND, defaultVal);
        }
        String msg = port.recvWithRetry();
        if (msg == null) {
            System.err.println("read: ZMQ recv timeout on port '" + portName + "'");
            return new ReadResult(ReadStatus.TIMEOUT, defaultVal);
        }
        s += msg;
        try {
            List<?> inval = (List<?>) literalEval(msg);
            if (!inval.isEmpty()) {
                simtime = Math.max(simtime, ((Number) inval.get(0)).doubleValue());
                return new ReadResult(ReadStatus.SUCCESS, new ArrayList<>(inval.subList(1, inval.size())));
            }
        } catch (Exception e) {
            System.out.println("Error parsing ZMQ message '" + msg + "': " + e.getMessage());
        }
        return new ReadResult(ReadStatus.PARSE_ERROR, defaultVal);
    }

    /**
     * Writes data to a ZMQ port. Prepends [simtime+delta] to match file-based write behavior.
     */
    public static void write(String portName, String name, Object val, int delta) {
        ZeroMQPort port = zmqPorts.get(portName);
        if (port == null) {
            System.err.println("write: ZMQ port '" + portName + "' not initialized");
            return;
        }
        String payload;
        if (val instanceof List) {
            List<?> listVal = (List<?>) val;
            StringBuilder sb = new StringBuilder("[");
            sb.append(toJsonLiteral(simtime + delta));
            for (Object o : listVal) {
                sb.append(", ");
                sb.append(toJsonLiteral(o));
            }
            sb.append("]");
            payload = sb.toString();
            // simtime must not be mutated here
        } else if (val instanceof String) {
            payload = (String) val;
        } else {
            System.out.println("write must have list or str");
            return;
        }
        port.sendWithRetry(payload);
    }

    /**
     * Parses a Python-literal string into Java objects using a recursive descent parser.
     * Supports: dict, list, int, float, string (single/double quoted), bool, None, nested structures.
     * This replaces the broken split-based parser that could not handle quoted commas or nesting.
     */
    static Object literalEval(String s) {
        if (s == null) throw new IllegalArgumentException("Input cannot be null");
        s = s.trim();
        if (s.isEmpty()) throw new IllegalArgumentException("Input cannot be empty");
        Parser parser = new Parser(s);
        Object result = parser.parseExpression();
        parser.skipWhitespace();
        if (parser.pos < parser.input.length()) {
            throw new IllegalArgumentException("Unexpected trailing content at position " + parser.pos);
        }
        return result;
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

    /**
     * ZMQ socket wrapper with bind/connect, timeouts, and retry.
     */
    private static class ZeroMQPort {
        final ZMQ.Socket socket;
        final String address;

        ZeroMQPort(String portType, String address, int socketType) {
            this.address = address;
            ZMQ.Context ctx = getZmqContext();
            this.socket = ctx.socket(socketType);
            this.socket.setReceiveTimeOut(2000);
            this.socket.setSendTimeOut(2000);
            this.socket.setLinger(0);
            if (portType.equals("bind")) {
                this.socket.bind(address);
            } else {
                this.socket.connect(address);
            }
        }

        String recvWithRetry() {
            for (int attempt = 0; attempt < 5; attempt++) {
                String msg = socket.recvStr();
                if (msg != null) return msg;
                try { Thread.sleep(500); } catch (InterruptedException e) { Thread.currentThread().interrupt(); break; }
            }
            return null;
        }

        void sendWithRetry(String message) {
            for (int attempt = 0; attempt < 5; attempt++) {
                if (socket.send(message)) return;
                try { Thread.sleep(500); } catch (InterruptedException e) { Thread.currentThread().interrupt(); break; }
            }
        }
    }

    /**
     * Recursive descent parser for Python literal expressions.
     * Handles: dicts, lists, tuples, strings, numbers, booleans, None.
     */
    private static class Parser {
        final String input;
        int pos;

        Parser(String input) {
            this.input = input;
            this.pos = 0;
        }

        void skipWhitespace() {
            while (pos < input.length() && Character.isWhitespace(input.charAt(pos))) {
                pos++;
            }
        }

        char peek() {
            skipWhitespace();
            if (pos >= input.length()) throw new IllegalArgumentException("Unexpected end of input");
            return input.charAt(pos);
        }

        char advance() {
            char c = input.charAt(pos);
            pos++;
            return c;
        }

        boolean hasMore() {
            skipWhitespace();
            return pos < input.length();
        }

        Object parseExpression() {
            skipWhitespace();
            if (pos >= input.length()) throw new IllegalArgumentException("Unexpected end of input");
            char c = input.charAt(pos);

            if (c == '{') return parseDict();
            if (c == '[') return parseList();
            if (c == '(') return parseTuple();
            if (c == '\'' || c == '"') return parseString();
            if (c == '-' || c == '+' || Character.isDigit(c)) return parseNumber();
            return parseKeyword();
        }

        Map<String, Object> parseDict() {
            Map<String, Object> map = new HashMap<>();
            pos++; // skip '{'
            skipWhitespace();
            if (hasMore() && input.charAt(pos) == '}') {
                pos++;
                return map;
            }
            while (true) {
                skipWhitespace();
                Object key = parseExpression();
                skipWhitespace();
                if (pos >= input.length() || input.charAt(pos) != ':') {
                    throw new IllegalArgumentException("Expected ':' in dict at position " + pos);
                }
                pos++; // skip ':'
                skipWhitespace();
                Object value = parseExpression();
                if (!(key instanceof String)) {
                    throw new IllegalArgumentException(
                        "Dict keys must be non-null strings, but got: "
                        + (key == null ? "null" : key.getClass().getSimpleName()));
                }
                map.put((String) key, value);
                skipWhitespace();
                if (pos >= input.length()) {
                    throw new IllegalArgumentException("Unterminated dict: missing '}'");
                }
                if (input.charAt(pos) == '}') {
                    pos++;
                    break;
                }
                if (input.charAt(pos) == ',') {
                    pos++;
                    skipWhitespace();
                    // trailing comma before close
                    if (hasMore() && input.charAt(pos) == '}') {
                        pos++;
                        break;
                    }
                } else {
                    throw new IllegalArgumentException("Expected ',' or '}' in dict at position " + pos);
                }
            }
            return map;
        }

        List<Object> parseList() {
            List<Object> list = new ArrayList<>();
            pos++; // skip '['
            skipWhitespace();
            if (hasMore() && input.charAt(pos) == ']') {
                pos++;
                return list;
            }
            while (true) {
                skipWhitespace();
                list.add(parseExpression());
                skipWhitespace();
                if (pos >= input.length()) {
                    throw new IllegalArgumentException("Unterminated list: missing ']'");
                }
                if (input.charAt(pos) == ']') {
                    pos++;
                    break;
                }
                if (input.charAt(pos) == ',') {
                    pos++;
                    skipWhitespace();
                    // trailing comma before close
                    if (hasMore() && input.charAt(pos) == ']') {
                        pos++;
                        break;
                    }
                } else {
                    throw new IllegalArgumentException("Expected ',' or ']' in list at position " + pos);
                }
            }
            return list;
        }

        List<Object> parseTuple() {
            List<Object> list = new ArrayList<>();
            pos++; // skip '('
            skipWhitespace();
            if (hasMore() && input.charAt(pos) == ')') {
                pos++;
                return list;
            }
            while (true) {
                skipWhitespace();
                list.add(parseExpression());
                skipWhitespace();
                if (pos >= input.length()) {
                    throw new IllegalArgumentException("Unterminated tuple: missing ')'");
                }
                if (input.charAt(pos) == ')') {
                    pos++;
                    break;
                }
                if (input.charAt(pos) == ',') {
                    pos++;
                    skipWhitespace();
                    // trailing comma before close
                    if (hasMore() && input.charAt(pos) == ')') {
                        pos++;
                        break;
                    }
                } else {
                    throw new IllegalArgumentException("Expected ',' or ')' in tuple at position " + pos);
                }
            }
            return list;
        }

        String parseString() {
            char quote = advance(); // opening quote
            StringBuilder sb = new StringBuilder();
            while (pos < input.length()) {
                char c = input.charAt(pos);
                if (c == '\\' && pos + 1 < input.length()) {
                    pos++;
                    char escaped = input.charAt(pos);
                    switch (escaped) {
                        case 'n': sb.append('\n'); break;
                        case 't': sb.append('\t'); break;
                        case 'r': sb.append('\r'); break;
                        case '\\': sb.append('\\'); break;
                        case '\'': sb.append('\''); break;
                        case '"': sb.append('"'); break;
                        default: sb.append('\\').append(escaped); break;
                    }
                    pos++;
                } else if (c == quote) {
                    pos++;
                    return sb.toString();
                } else {
                    sb.append(c);
                    pos++;
                }
            }
            throw new IllegalArgumentException("Unterminated string starting at position " + (pos - sb.length() - 1));
        }

        Number parseNumber() {
            int start = pos;
            if (pos < input.length() && (input.charAt(pos) == '-' || input.charAt(pos) == '+')) {
                pos++;
            }
            boolean hasDecimal = false;
            boolean hasExponent = false;
            while (pos < input.length()) {
                char c = input.charAt(pos);
                if (Character.isDigit(c)) {
                    pos++;
                } else if (c == '.' && !hasDecimal && !hasExponent) {
                    hasDecimal = true;
                    pos++;
                } else if ((c == 'e' || c == 'E') && !hasExponent) {
                    hasExponent = true;
                    pos++;
                    if (pos < input.length() && (input.charAt(pos) == '+' || input.charAt(pos) == '-')) {
                        pos++;
                    }
                } else {
                    break;
                }
            }
            String numStr = input.substring(start, pos);
            try {
                if (hasDecimal || hasExponent) {
                    return Double.parseDouble(numStr);
                } else {
                    try {
                        return Integer.parseInt(numStr);
                    } catch (NumberFormatException e) {
                        return Long.parseLong(numStr);
                    }
                }
            } catch (NumberFormatException e) {
                throw new IllegalArgumentException("Invalid number: '" + numStr + "' at position " + start);
            }
        }

        Object parseKeyword() {
            int start = pos;
            while (pos < input.length() && Character.isLetterOrDigit(input.charAt(pos)) || (pos < input.length() && input.charAt(pos) == '_')) {
                pos++;
            }
            String word = input.substring(start, pos);
            switch (word) {
                case "True":  case "true":  return Boolean.TRUE;
                case "False": case "false": return Boolean.FALSE;
                case "None":  case "null":  return null;
                default: throw new IllegalArgumentException("Unknown keyword: '" + word + "' at position " + start);
            }
        }
    }
}
