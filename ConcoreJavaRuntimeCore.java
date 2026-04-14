import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.zeromq.ZMQ;

class ConcoreJavaRuntimeCore {
    private Map<String, Object> iport = new HashMap<>();
    private Map<String, Object> oport = new HashMap<>();
    private String s = "";
    private String olds = "";
    private int delay = 1000;
    private int retrycount = 0;
    private int maxRetries = 5;
    private String inpath;
    private String outpath;
    private final boolean suffixPortPath;
    private Map<String, Object> params = new HashMap<>();
    private Map<String, ZeroMQPort> zmqPorts = new HashMap<>();
    private ZMQ.Context zmqContext = null;
    private double simtime = 0;
    private double maxtime;

    ConcoreJavaRuntimeCore(String inpath, String outpath, boolean suffixPortPath) {
        this.inpath = inpath;
        this.outpath = outpath;
        this.suffixPortPath = suffixPortPath;
        initialize();
    }

    private void initialize() {
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
            if (sparams.length() > 0 && sparams.charAt(0) == '"') {
                sparams = sparams.substring(1);
                sparams = sparams.substring(0, sparams.indexOf('"'));
            }
            params = parseParams(sparams);
        } catch (IOException e) {
            params = new HashMap<>();
        }
        defaultMaxTime(100);
    }

    private String portPath(String base, int portNum) {
        if (suffixPortPath) {
            return base + portNum;
        }
        return Paths.get(base, String.valueOf(portNum)).toString();
    }

    private Path resolvePortFilePath(String base, int portNum, String name) throws IOException {
        Path portDir = Paths.get(portPath(base, portNum)).toAbsolutePath().normalize();
        Path filePath = portDir.resolve(name).normalize();
        if (!filePath.startsWith(portDir)) {
            throw new IOException("Invalid file name '" + name + "' for port " + portNum);
        }
        return filePath;
    }

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
                String[] parts = item.split("=", 2);
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

    void setInPath(String path) { inpath = path; }
    void setOutPath(String path) { outpath = path; }
    void setDelay(int ms) { delay = ms; }
    double getSimtime() { return simtime; }
    void resetState() { s = ""; olds = ""; simtime = 0; }

    boolean unchanged() {
        if (olds.equals(s)) {
            s = "";
            return true;
        }
        olds = s;
        return false;
    }

    Object tryParam(String n, Object i) {
        if (params.containsKey(n)) {
            return params.get(n);
        }
        return i;
    }

    void defaultMaxTime(double defaultValue) {
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

    ReadResult readFilePort(int port, String name, String initstr) {
        List<Object> defaultVal = new ArrayList<>();
        try {
            List<?> parsed = (List<?>) literalEval(initstr);
            if (parsed.size() > 1) {
                defaultVal = new ArrayList<>(parsed.subList(1, parsed.size()));
            }
        } catch (Exception e) {
        }

        Path filePathObj;
        try {
            filePathObj = resolvePortFilePath(inpath, port, name);
        } catch (IOException | RuntimeException e) {
            System.out.println("Invalid path for port " + port + " and name '" + name + "': " + e.getMessage());
            return new ReadResult(ReadStatus.PARSE_ERROR, defaultVal);
        }
        String filePath = filePathObj.toString();
        try {
            Thread.sleep(delay);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            s += initstr;
            return new ReadResult(ReadStatus.TIMEOUT, defaultVal);
        }

        String ins;
        try {
            ins = new String(Files.readAllBytes(filePathObj));
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
                ins = new String(Files.readAllBytes(filePathObj));
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

    void writeFilePort(int port, String name, Object val, int delta) {
        try {
            Path pathObj = resolvePortFilePath(outpath, port, name);
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
            } else if (val instanceof Object[]) {
                Object[] arrayVal = (Object[]) val;
                content.append("[");
                content.append(toPythonLiteral(simtime + delta));
                for (Object o : arrayVal) {
                    content.append(", ");
                    content.append(toPythonLiteral(o));
                }
                content.append("]");
            } else {
                System.out.println("write must have list or str");
                return;
            }
            Files.write(pathObj, content.toString().getBytes());
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            System.out.println("skipping " + outpath + "/" + port + "/" + name);
        } catch (IOException e) {
            System.out.println("skipping " + outpath + "/" + port + "/" + name);
        }
    }

    List<Object> initVal(String simtimeVal) {
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

    private ZMQ.Context getZmqContext() {
        if (zmqContext == null) {
            zmqContext = ZMQ.context(1);
        }
        return zmqContext;
    }

    void initZmqPort(String portName, String portType, String address, String socketTypeStr) {
        if (zmqPorts.containsKey(portName)) return;
        int sockType = zmqSocketTypeFromString(socketTypeStr);
        if (sockType == -1) {
            System.err.println("initZmqPort: unknown socket type '" + socketTypeStr + "'");
            return;
        }
        zmqPorts.put(portName, new ZeroMQPort(portType, address, sockType));
    }

    void terminateZmq() {
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

    ReadResult readZmqPort(String portName, String name, String initstr) {
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

    void writeZmqPort(String portName, String name, Object val, int delta) {
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
        } else if (val instanceof String) {
            payload = (String) val;
        } else {
            System.out.println("write must have list or str");
            return;
        }
        port.sendWithRetry(payload);
    }

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

    enum ReadStatus {
        SUCCESS, FILE_NOT_FOUND, TIMEOUT, PARSE_ERROR, RETRIES_EXCEEDED
    }

    static class ReadResult {
        final ReadStatus status;
        final List<Object> data;
        ReadResult(ReadStatus status, List<Object> data) {
            this.status = status;
            this.data = data;
        }
    }

    private class ZeroMQPort {
        final ZMQ.Socket socket;

        ZeroMQPort(String portType, String address, int socketType) {
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

        boolean hasMore() {
            skipWhitespace();
            return pos < input.length();
        }

        char advance() {
            char c = input.charAt(pos);
            pos++;
            return c;
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
            pos++;
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
                pos++;
                skipWhitespace();
                Object value = parseExpression();
                if (!(key instanceof String)) {
                    throw new IllegalArgumentException("Dict keys must be non-null strings, but got: "
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
            pos++;
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
            pos++;
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
            char quote = advance();
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
                }
                try {
                    return Integer.parseInt(numStr);
                } catch (NumberFormatException e) {
                    return Long.parseLong(numStr);
                }
            } catch (NumberFormatException e) {
                throw new IllegalArgumentException("Invalid number: '" + numStr + "' at position " + start);
            }
        }

        Object parseKeyword() {
            int start = pos;
            while ((pos < input.length() && Character.isLetterOrDigit(input.charAt(pos)))
                    || (pos < input.length() && input.charAt(pos) == '_')) {
                pos++;
            }
            String word = input.substring(start, pos);
            switch (word) {
                case "True":
                case "true":
                    return Boolean.TRUE;
                case "False":
                case "false":
                    return Boolean.FALSE;
                case "None":
                case "null":
                    return null;
                default:
                    throw new IllegalArgumentException("Unknown keyword: '" + word + "' at position " + start);
            }
        }
    }
}