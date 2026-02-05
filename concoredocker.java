import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.HashMap;
import java.util.Map;

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

    public static void main(String[] args) {
        try {
            iport = parseFile("concore.iport");
        } catch (IOException e) {
            e.printStackTrace();
        }
        try {
            oport = parseFile("concore.oport");
        } catch (IOException e) {
            e.printStackTrace();
        }

        try {
            String sparams = new String(Files.readAllBytes(Paths.get(inpath + "1/concore.params")));
            if (sparams.charAt(0) == '"') { // windows keeps "" need to remove
                sparams = sparams.substring(1);
                sparams = sparams.substring(0, sparams.indexOf('"'));
            }
            if (!sparams.equals("{")) {
                System.out.println("converting sparams: " + sparams);
                sparams = "{'" + sparams.replaceAll(",", ",'").replaceAll("=", "':").replaceAll(" ", "") + "}";
                System.out.println("converted sparams: " + sparams);
            }
            try {
                params = literalEval(sparams);
            } catch (Exception e) {
                System.out.println("bad params: " + sparams);
            }
        } catch (IOException e) {
            params = new HashMap<>();
        }

        defaultMaxTime(100);
    }

    private static Map<String, Object> parseFile(String filename) throws IOException {
        String content = new String(Files.readAllBytes(Paths.get(filename)));
        return literalEval(content);
    }

    private static void defaultMaxTime(int defaultValue) {
        try {
            String content = new String(Files.readAllBytes(Paths.get(inpath + "1/concore.maxtime"))).trim();
            Object val = parsePythonLiteral(content);
            if (val instanceof Number) {
                maxtime = ((Number) val).intValue();
            } else {
                maxtime = defaultValue;
            }
        } catch (IOException e) {
            maxtime = defaultValue;
        }
    }

    private static void unchanged() {
        if (olds.equals(s)) {
            s = "";
        } else {
            olds = s;
        }
    }

    private static Object tryParam(String n, Object i) {
        if (params.containsKey(n)) {
            return params.get(n);
        } else {
            return i;
        }
    }

    private static Object read(int port, String name, String initstr) {
        try {
            String ins = new String(Files.readAllBytes(Paths.get(inpath + port + "/" + name)));
            while (ins.length() == 0) {
                Thread.sleep(delay);
                ins = new String(Files.readAllBytes(Paths.get(inpath + port + "/" + name)));
                retrycount++;
            }
            s += ins;
            Object[] inval = literalEvalList(ins);
            if (inval.length > 0) {
                int simtime = ((Number) inval[0]).intValue();
                if (inval.length > 1) {
                    Object[] result = new Object[inval.length - 1];
                    System.arraycopy(inval, 1, result, 0, result.length);
                    return result;
                }
            }
            return initstr;
        } catch (IOException | InterruptedException e) {
            return initstr;
        }
    }

    private static void write(int port, String name, Object val, int delta) {
        try {
            String path = outpath + port + "/" + name;
            StringBuilder content = new StringBuilder();
            if (val instanceof String) {
                Thread.sleep(2 * delay);
            } else if (!(val instanceof Object[])) {
                System.out.println("mywrite must have list or str");
                System.exit(1);
            }
            if (val instanceof Object[]) {
                Object[] arrayVal = (Object[]) val;
                content.append("[")
                        .append(maxtime + delta)
                        .append(",")
                        .append(arrayVal[0]);
                for (int i = 1; i < arrayVal.length; i++) {
                    content.append(",")
                            .append(arrayVal[i]);
                }
                content.append("]");
            } else {
                content.append(val);
            }
            Files.write(Paths.get(path), content.toString().getBytes());
        } catch (IOException | InterruptedException e) {
            System.out.println("skipping" + outpath + port + "/" + name);
        }
    }

    private static Object[] initVal(String simtimeVal) {
        Object[] val = new Object[] {};
        try {
            Object[] arrayVal = literalEvalList(simtimeVal);
            if (arrayVal.length > 1) {
                val = new Object[arrayVal.length - 1];
                System.arraycopy(arrayVal, 1, val, 0, val.length);
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
        return val;
    }

    private static Map<String, Object> literalEval(String s) {
        Object result = parsePythonLiteral(s);
        if (result instanceof Map) {
            return (Map<String, Object>) result;
        }
        return new HashMap<>();
    }

    private static Object[] literalEvalList(String s) {
        Object result = parsePythonLiteral(s);
        if (result instanceof Object[]) {
            return (Object[]) result;
        }
        return new Object[]{};
    }

    private static Object parsePythonLiteral(String s) {
        if (s == null) return null;
        s = s.trim();
        if (s.isEmpty()) return null;

        // dict: {'key': value, ...}
        if (s.startsWith("{") && s.endsWith("}")) {
            return parseDict(s.substring(1, s.length() - 1));
        }
        // list: [val1, val2, ...]
        if (s.startsWith("[") && s.endsWith("]")) {
            return parseList(s.substring(1, s.length() - 1));
        }
        // single value
        return parseValue(s);
    }

    private static Map<String, Object> parseDict(String inner) {
        Map<String, Object> map = new HashMap<>();
        if (inner.trim().isEmpty()) return map;

        int i = 0;
        while (i < inner.length()) {
            // skip whitespace
            while (i < inner.length() && Character.isWhitespace(inner.charAt(i))) i++;
            if (i >= inner.length()) break;

            // parse key (quoted string)
            char quote = inner.charAt(i);
            if (quote != '\'' && quote != '"') break;
            i++;
            int keyStart = i;
            while (i < inner.length() && inner.charAt(i) != quote) i++;
            String key = inner.substring(keyStart, i);
            i++; // skip closing quote

            // skip to colon
            while (i < inner.length() && inner.charAt(i) != ':') i++;
            i++; // skip colon

            // skip whitespace
            while (i < inner.length() && Character.isWhitespace(inner.charAt(i))) i++;

            // parse value
            int[] endIdx = new int[]{i};
            Object val = parseValueAt(inner, endIdx);
            i = endIdx[0];
            map.put(key, val);

            // skip to comma or end
            while (i < inner.length() && inner.charAt(i) != ',') i++;
            i++; // skip comma
        }
        return map;
    }

    private static Object[] parseList(String inner) {
        if (inner.trim().isEmpty()) return new Object[]{};

        java.util.List<Object> list = new java.util.ArrayList<>();
        int i = 0;
        while (i < inner.length()) {
            while (i < inner.length() && Character.isWhitespace(inner.charAt(i))) i++;
            if (i >= inner.length()) break;

            int[] endIdx = new int[]{i};
            Object val = parseValueAt(inner, endIdx);
            i = endIdx[0];
            list.add(val);

            while (i < inner.length() && (Character.isWhitespace(inner.charAt(i)) || inner.charAt(i) == ',')) i++;
        }
        return list.toArray();
    }

    private static Object parseValueAt(String s, int[] idx) {
        int i = idx[0];
        while (i < s.length() && Character.isWhitespace(s.charAt(i))) i++;
        if (i >= s.length()) {
            idx[0] = i;
            return null;
        }

        char c = s.charAt(i);
        // nested dict
        if (c == '{') {
            int depth = 1, start = i;
            i++;
            while (i < s.length() && depth > 0) {
                if (s.charAt(i) == '{') depth++;
                else if (s.charAt(i) == '}') depth--;
                i++;
            }
            idx[0] = i;
            return parsePythonLiteral(s.substring(start, i));
        }
        // nested list
        if (c == '[') {
            int depth = 1, start = i;
            i++;
            while (i < s.length() && depth > 0) {
                if (s.charAt(i) == '[') depth++;
                else if (s.charAt(i) == ']') depth--;
                i++;
            }
            idx[0] = i;
            return parsePythonLiteral(s.substring(start, i));
        }
        // quoted string
        if (c == '\'' || c == '"') {
            char quote = c;
            i++;
            int start = i;
            while (i < s.length() && s.charAt(i) != quote) i++;
            String val = s.substring(start, i);
            i++; // skip closing quote
            idx[0] = i;
            return val;
        }
        // number or other
        int start = i;
        while (i < s.length() && s.charAt(i) != ',' && s.charAt(i) != '}' && s.charAt(i) != ']' && !Character.isWhitespace(s.charAt(i))) {
            i++;
        }
        idx[0] = i;
        return parseValue(s.substring(start, i));
    }

    private static Object parseValue(String s) {
        s = s.trim();
        if (s.isEmpty()) return null;
        if (s.equals("None") || s.equals("null")) return null;
        if (s.equals("True") || s.equals("true")) return true;
        if (s.equals("False") || s.equals("false")) return false;
        try {
            if (s.contains(".")) return Double.parseDouble(s);
            return Integer.parseInt(s);
        } catch (NumberFormatException e) {
            return s;
        }
    }
}

