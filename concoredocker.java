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
            String content = new String(Files.readAllBytes(Paths.get(inpath + "1/concore.maxtime")));
            maxtime = literalEval(content).size();
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
            Object[] inval = new Map[] { literalEval(ins) };
            int simtime = Math.max((int) inval[0], 0); // assuming simtime is an integer
            return inval[1];
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
        int simtime = 0;
        Object[] val = new Object[] {};
        try {
            Object[] arrayVal = new Map[] { literalEval(simtimeVal) };
            simtime = (int) arrayVal[0]; // assuming simtime is an integer
            val = new Object[arrayVal.length - 1];
            System.arraycopy(arrayVal, 1, val, 0, val.length);
        } catch (Exception e) {
            e.printStackTrace();
        }
        return val;
    }

    private static Map<String, Object> literalEval(String s) {

        return new HashMap<>();
    }
}
