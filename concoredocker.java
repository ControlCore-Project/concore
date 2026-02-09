import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Java implementation of concore Docker communication.
 * 
 * This class provides file-based inter-process communication for control systems,
 * mirroring the functionality of concoredocker.py.
 */
public class concoredocker {
    private static Map<String, Object> iport = new HashMap<>();
    private static Map<String, Object> oport = new HashMap<>();
    private static String s = "";
    private static String olds = "";
    private static int delay = 1;
    private static int retrycount = 0;
    private static String inpath = "/in";
    private static String outpath = "/out";
    private static Map<String, Object> params = new HashMap<>();
    private static int maxtime;
    private static int simtime = 0;

    public static void main(String[] args) {
        try {
            iport = parseFileAsMap("concore.iport");
        } catch (IOException e) {
            e.printStackTrace();
        }
        try {
            oport = parseFileAsMap("concore.oport");
        } catch (IOException e) {
            e.printStackTrace();
        }

        try {
            String sparams = new String(Files.readAllBytes(Paths.get(inpath + "1/concore.params")));
            if (sparams.length() > 0 && sparams.charAt(0) == '"') { // windows keeps "" need to remove
                sparams = sparams.substring(1);
                sparams = sparams.substring(0, sparams.indexOf('"'));
            }
            if (!sparams.equals("{")) {
                System.out.println("converting sparams: " + sparams);
                sparams = "{'" + sparams.replaceAll(",", ",'").replaceAll("=", "':").replaceAll(" ", "") + "}";
                System.out.println("converted sparams: " + sparams);
            }
            try {
                Object parsed = literalEval(sparams);
                if (parsed instanceof Map) {
                    @SuppressWarnings("unchecked")
                    Map<String, Object> parsedMap = (Map<String, Object>) parsed;
                    params = parsedMap;
                }
            } catch (Exception e) {
                System.out.println("bad params: " + sparams);
            }
        } catch (IOException e) {
            params = new HashMap<>();
        }

        defaultMaxTime(100);
    }

    /**
     * Parses a file containing a Python-style dictionary literal.
     */
    private static Map<String, Object> parseFileAsMap(String filename) throws IOException {
        String content = new String(Files.readAllBytes(Paths.get(filename)));
        Object result = literalEval(content);
        if (result instanceof Map) {
            @SuppressWarnings("unchecked")
            Map<String, Object> map = (Map<String, Object>) result;
            return map;
        }
        return new HashMap<>();
    }

    /**
     * Sets maxtime from concore.maxtime file, or uses defaultValue if file not found.
     * The file contains a simple integer value.
     */
    private static void defaultMaxTime(int defaultValue) {
        try {
            String content = new String(Files.readAllBytes(Paths.get(inpath + "1/concore.maxtime")));
            Object parsed = literalEval(content.trim());
            if (parsed instanceof Number) {
                maxtime = ((Number) parsed).intValue();
            } else {
                maxtime = defaultValue;
            }
        } catch (IOException e) {
            maxtime = defaultValue;
        }
    }

    /**
     * Checks if the accumulated input string has changed since last call.
     * Returns true if unchanged (and clears s), false if changed (and updates olds).
     * This matches the Python implementation semantics.
     */
    private static boolean unchanged() {
        if (olds.equals(s)) {
            s = "";
            return true;
        }
        olds = s;
        return false;
    }

    private static Object tryParam(String n, Object i) {
        if (params.containsKey(n)) {
            return params.get(n);
        } else {
            return i;
        }
    }

    /**
     * Reads data from a port file. Returns the values after extracting simtime.
     * Input format: [simtime, val1, val2, ...]
     * Returns: [val1, val2, ...] as List
     */
    private static Object read(int port, String name, String initstr) {
        try {
            String ins = new String(Files.readAllBytes(Paths.get(inpath + port + "/" + name)));
            while (ins.length() == 0) {
                Thread.sleep(delay);
                ins = new String(Files.readAllBytes(Paths.get(inpath + port + "/" + name)));
                retrycount++;
            }
            s += ins;
            Object parsed = literalEval(ins);
            if (parsed instanceof List) {
                @SuppressWarnings("unchecked")
                List<Object> inval = (List<Object>) parsed;
                if (!inval.isEmpty()) {
                    // First element is simtime
                    Object first = inval.get(0);
                    if (first instanceof Number) {
                        simtime = Math.max(simtime, ((Number) first).intValue());
                    }
                    // Return remaining elements (values after simtime)
                    return inval.subList(1, inval.size());
                }
            }
            return initstr;
        } catch (IOException | InterruptedException e) {
            return initstr;
        }
    }

    /**
     * Writes data to a port file.
     * Output format: [simtime + delta, val1, val2, ...]
     */
    private static void write(int port, String name, Object val, int delta) {
        try {
            String path = outpath + port + "/" + name;
            StringBuilder content = new StringBuilder();
            if (val instanceof String) {
                Thread.sleep(2 * delay);
                content.append(val);
            } else if (val instanceof List) {
                @SuppressWarnings("unchecked")
                List<Object> listVal = (List<Object>) val;
                content.append("[").append(simtime + delta);
                for (Object item : listVal) {
                    content.append(",").append(item);
                }
                content.append("]");
                simtime += delta;
            } else if (val instanceof Object[]) {
                Object[] arrayVal = (Object[]) val;
                content.append("[").append(simtime + delta);
                for (Object item : arrayVal) {
                    content.append(",").append(item);
                }
                content.append("]");
                simtime += delta;
            } else {
                System.out.println("write must have list or str");
                return;
            }
            Files.write(Paths.get(path), content.toString().getBytes());
        } catch (IOException | InterruptedException e) {
            System.out.println("skipping " + outpath + port + "/" + name);
        }
    }

    /**
     * Parses an initial value string and extracts values after simtime.
     * Input format: "[simtime, val1, val2, ...]"
     * Returns: [val1, val2, ...] as List
     */
    private static List<Object> initVal(String simtimeVal) {
        try {
            Object parsed = literalEval(simtimeVal);
            if (parsed instanceof List) {
                @SuppressWarnings("unchecked")
                List<Object> val = (List<Object>) parsed;
                if (!val.isEmpty()) {
                    Object first = val.get(0);
                    if (first instanceof Number) {
                        simtime = ((Number) first).intValue();
                    }
                    return val.subList(1, val.size());
                }
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
        return new ArrayList<>();
    }

    /**
     * Parses a Python-style literal string and returns the corresponding Java object.
     * 
     * Supports:
     * - Dictionaries: {'key': value, ...} -> Map<String, Object>
     * - Lists: [val1, val2, ...] -> List<Object>
     * - Numbers: 42, 3.14 -> Integer or Double
     * - Strings: 'hello' or "hello" -> String
     * - Booleans: True, False -> Boolean
     * - None -> null
     * 
     * This implementation replaces the previous stub that always returned an empty HashMap,
     * which caused read(), defaultMaxTime(), write(), and initVal() to silently fail.
     * 
     * @param input The Python literal string to parse
     * @return The parsed Java object (Map, List, Number, String, Boolean, or null)
     * @throws IllegalArgumentException if the input cannot be parsed
     */
    private static Object literalEval(String input) {
        if (input == null) {
            throw new IllegalArgumentException("Cannot parse null input");
        }
        Parser parser = new Parser(input.trim());
        Object result = parser.parseValue();
        parser.skipWhitespace();
        if (parser.hasMore()) {
            throw new IllegalArgumentException("Unexpected characters after parsed value: " + parser.remaining());
        }
        return result;
    }

    /**
     * Simple recursive descent parser for Python-style literals.
     */
    private static class Parser {
        private final String input;
        private int pos = 0;

        Parser(String input) {
            this.input = input;
        }

        boolean hasMore() {
            return pos < input.length();
        }

        String remaining() {
            return input.substring(pos);
        }

        char peek() {
            if (!hasMore()) {
                throw new IllegalArgumentException("Unexpected end of input");
            }
            return input.charAt(pos);
        }

        char consume() {
            return input.charAt(pos++);
        }

        void skipWhitespace() {
            while (hasMore() && Character.isWhitespace(input.charAt(pos))) {
                pos++;
            }
        }

        void expect(char c) {
            skipWhitespace();
            if (!hasMore() || consume() != c) {
                throw new IllegalArgumentException("Expected '" + c + "' at position " + (pos - 1));
            }
        }

        Object parseValue() {
            skipWhitespace();
            if (!hasMore()) {
                throw new IllegalArgumentException("Unexpected end of input");
            }
            char c = peek();
            if (c == '{') {
                return parseDict();
            } else if (c == '[') {
                return parseList();
            } else if (c == '\'' || c == '"') {
                return parseString();
            } else if (c == '-' || Character.isDigit(c)) {
                return parseNumber();
            } else if (input.substring(pos).startsWith("True")) {
                pos += 4;
                return Boolean.TRUE;
            } else if (input.substring(pos).startsWith("False")) {
                pos += 5;
                return Boolean.FALSE;
            } else if (input.substring(pos).startsWith("None")) {
                pos += 4;
                return null;
            } else {
                throw new IllegalArgumentException("Unexpected character '" + c + "' at position " + pos);
            }
        }

        Map<String, Object> parseDict() {
            Map<String, Object> map = new HashMap<>();
            expect('{');
            skipWhitespace();
            if (hasMore() && peek() == '}') {
                consume();
                return map;
            }
            while (true) {
                skipWhitespace();
                // Parse key (must be a string)
                String key;
                char c = peek();
                if (c == '\'' || c == '"') {
                    key = parseString();
                } else {
                    throw new IllegalArgumentException("Dictionary key must be a string at position " + pos);
                }
                skipWhitespace();
                expect(':');
                Object value = parseValue();
                map.put(key, value);
                skipWhitespace();
                if (!hasMore()) {
                    throw new IllegalArgumentException("Unexpected end of input in dictionary");
                }
                c = peek();
                if (c == '}') {
                    consume();
                    break;
                } else if (c == ',') {
                    consume();
                } else {
                    throw new IllegalArgumentException("Expected ',' or '}' at position " + pos);
                }
            }
            return map;
        }

        List<Object> parseList() {
            List<Object> list = new ArrayList<>();
            expect('[');
            skipWhitespace();
            if (hasMore() && peek() == ']') {
                consume();
                return list;
            }
            while (true) {
                list.add(parseValue());
                skipWhitespace();
                if (!hasMore()) {
                    throw new IllegalArgumentException("Unexpected end of input in list");
                }
                char c = peek();
                if (c == ']') {
                    consume();
                    break;
                } else if (c == ',') {
                    consume();
                } else {
                    throw new IllegalArgumentException("Expected ',' or ']' at position " + pos);
                }
            }
            return list;
        }

        String parseString() {
            char quote = consume(); // ' or "
            StringBuilder sb = new StringBuilder();
            while (hasMore()) {
                char c = consume();
                if (c == quote) {
                    return sb.toString();
                } else if (c == '\\' && hasMore()) {
                    char escaped = consume();
                    switch (escaped) {
                        case 'n': sb.append('\n'); break;
                        case 't': sb.append('\t'); break;
                        case 'r': sb.append('\r'); break;
                        case '\\': sb.append('\\'); break;
                        case '\'': sb.append('\''); break;
                        case '"': sb.append('"'); break;
                        default: sb.append(escaped); break;
                    }
                } else {
                    sb.append(c);
                }
            }
            throw new IllegalArgumentException("Unterminated string");
        }

        Number parseNumber() {
            int start = pos;
            boolean isFloat = false;
            if (peek() == '-') {
                consume();
            }
            while (hasMore() && Character.isDigit(peek())) {
                consume();
            }
            if (hasMore() && peek() == '.') {
                isFloat = true;
                consume();
                while (hasMore() && Character.isDigit(peek())) {
                    consume();
                }
            }
            // Handle scientific notation
            if (hasMore() && (peek() == 'e' || peek() == 'E')) {
                isFloat = true;
                consume();
                if (hasMore() && (peek() == '+' || peek() == '-')) {
                    consume();
                }
                while (hasMore() && Character.isDigit(peek())) {
                    consume();
                }
            }
            String numStr = input.substring(start, pos);
            if (isFloat) {
                return Double.parseDouble(numStr);
            } else {
                try {
                    return Integer.parseInt(numStr);
                } catch (NumberFormatException e) {
                    return Long.parseLong(numStr);
                }
            }
        }
    }
}
