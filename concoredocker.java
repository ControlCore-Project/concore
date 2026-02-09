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
    // delay in milliseconds (Python uses time.sleep(1) = 1 second)
    private static int delay = 1000;
    private static int retrycount = 0;
    private static int maxRetries = 5;
    private static String inpath = "/in";
    private static String outpath = "/out";
    private static Map<String, Object> params = new HashMap<>();
    private static int maxtime;
    // simtime as double to preserve fractional values (matches Python behavior)
    private static double simtime = 0;

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
     * Returns empty map if file is empty or malformed (matches Python safe_literal_eval behavior).
     */
    private static Map<String, Object> parseFileAsMap(String filename) throws IOException {
        String content = new String(Files.readAllBytes(Paths.get(filename)));
        content = content.trim();
        if (content.isEmpty()) {
            // Empty file: treat as empty map
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
            // Malformed content: log and fall back to empty map
            System.err.println("Failed to parse file as map: " + filename + " (" + e.getMessage() + ")");
        }
        return new HashMap<>();
    }

    /**
     * Sets maxtime from concore.maxtime file, or uses defaultValue if file not found.
     * The file contains a simple integer value.
     * Catches both IOException (file not found) and RuntimeException (parse errors)
     * to match Python safe_literal_eval behavior.
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
        } catch (IOException | RuntimeException e) {
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
     * Includes max retry limit to avoid infinite blocking (matches Python behavior).
     */
    private static Object read(int port, String name, String initstr) {
        String filePath = inpath + port + "/" + name;
        try {
            Thread.sleep(delay);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            return initstr;
        }
        
        String ins;
        try {
            ins = new String(Files.readAllBytes(Paths.get(filePath)));
        } catch (IOException e) {
            System.out.println("File " + filePath + " not found, using default value.");
            return initstr;
        }
        
        int attempts = 0;
        while (ins.length() == 0 && attempts < maxRetries) {
            try {
                Thread.sleep(delay);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                return initstr;
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
            return initstr;
        }
        
        s += ins;
        try {
            Object parsed = literalEval(ins);
            if (parsed instanceof List) {
                @SuppressWarnings("unchecked")
                List<Object> inval = (List<Object>) parsed;
                if (!inval.isEmpty()) {
                    // First element is simtime (preserve as double for fractional values)
                    Object first = inval.get(0);
                    if (first instanceof Number) {
                        double firstSimtime = ((Number) first).doubleValue();
                        simtime = Math.max(simtime, firstSimtime);
                    }
                    // Return remaining elements (values after simtime)
                    return inval.subList(1, inval.size());
                }
            }
        } catch (IllegalArgumentException e) {
            System.out.println("Error parsing " + ins + ": " + e.getMessage());
        }
        return initstr;
    }

    /**
     * Writes data to a port file.
     * Output format: [simtime + delta, val1, val2, ...]
     * Uses Python-literal-compatible serialization for proper interoperability.
     */
    private static void write(int port, String name, Object val, int delta) {
        String path = outpath + port + "/" + name;
        StringBuilder content = new StringBuilder();
        
        if (val instanceof String) {
            try {
                Thread.sleep(2 * delay);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                return;
            }
            content.append(val);
        } else if (val instanceof List) {
            @SuppressWarnings("unchecked")
            List<Object> listVal = (List<Object>) val;
            content.append("[").append(simtime + delta);
            for (Object item : listVal) {
                content.append(",").append(toPythonLiteral(item));
            }
            content.append("]");
            simtime += delta;
        } else if (val instanceof Object[]) {
            Object[] arrayVal = (Object[]) val;
            content.append("[").append(simtime + delta);
            for (Object item : arrayVal) {
                content.append(",").append(toPythonLiteral(item));
            }
            content.append("]");
            simtime += delta;
        } else {
            System.out.println("write must have list or str");
            return;
        }
        
        try {
            Files.write(Paths.get(path), content.toString().getBytes());
        } catch (IOException e) {
            System.out.println("Error writing to " + path + ": " + e.getMessage());
        }
    }

    /**
     * Converts a Java object to its Python-literal-compatible string representation.
     * This ensures proper interoperability when the receiving side parses the output.
     */
    private static String toPythonLiteral(Object obj) {
        if (obj == null) {
            return "None";
        } else if (obj instanceof Boolean) {
            return ((Boolean) obj) ? "True" : "False";
        } else if (obj instanceof String) {
            // Quote strings and escape special characters
            String s = (String) obj;
            StringBuilder sb = new StringBuilder("'");
            for (char c : s.toCharArray()) {
                switch (c) {
                    case '\'': sb.append("\\'"); break;
                    case '\\': sb.append("\\\\"); break;
                    case '\n': sb.append("\\n"); break;
                    case '\r': sb.append("\\r"); break;
                    case '\t': sb.append("\\t"); break;
                    default: sb.append(c); break;
                }
            }
            sb.append("'");
            return sb.toString();
        } else if (obj instanceof Number) {
            return obj.toString();
        } else if (obj instanceof List) {
            @SuppressWarnings("unchecked")
            List<Object> list = (List<Object>) obj;
            StringBuilder sb = new StringBuilder("[");
            for (int i = 0; i < list.size(); i++) {
                if (i > 0) sb.append(", ");
                sb.append(toPythonLiteral(list.get(i)));
            }
            sb.append("]");
            return sb.toString();
        } else if (obj instanceof Map) {
            @SuppressWarnings("unchecked")
            Map<String, Object> map = (Map<String, Object>) obj;
            StringBuilder sb = new StringBuilder("{");
            boolean first = true;
            for (Map.Entry<String, Object> entry : map.entrySet()) {
                if (!first) sb.append(", ");
                first = false;
                sb.append(toPythonLiteral(entry.getKey())).append(": ").append(toPythonLiteral(entry.getValue()));
            }
            sb.append("}");
            return sb.toString();
        } else {
            // Fallback: use toString()
            return obj.toString();
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
                        // Preserve fractional simtime values
                        simtime = ((Number) first).doubleValue();
                    }
                    return val.subList(1, val.size());
                }
            }
        } catch (Exception e) {
            System.out.println("Error parsing simtime_val: " + e.getMessage());
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
                try {
                    return Double.parseDouble(numStr);
                } catch (NumberFormatException e) {
                    throw new IllegalArgumentException("Invalid numeric value: " + numStr, e);
                }
            } else {
                try {
                    return Integer.parseInt(numStr);
                } catch (NumberFormatException e) {
                    try {
                        return Long.parseLong(numStr);
                    } catch (NumberFormatException e2) {
                        throw new IllegalArgumentException("Invalid numeric value: " + numStr, e2);
                    }
                }
            }
        }
    }
}
