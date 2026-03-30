import java.util.ArrayList;
import java.util.List;

public class pm_java {
    private static final String INIT_SIMTIME_U = "[0.0, 0.0]";

    private static double toDouble(Object value) {
        if (value instanceof Number) {
            return ((Number) value).doubleValue();
        }
        return 0.0;
    }

    public static void main(String[] args) {
        String studyDir = System.getenv("CONCORE_STUDY_DIR");
        if (studyDir == null || studyDir.isEmpty()) {
            studyDir = "example/java_e2e/study";
        }
        double maxTime = 20.0;

        concoredocker.setInPath(studyDir);
        concoredocker.setOutPath(studyDir);
        concoredocker.setDelay(20);
        concoredocker.defaultMaxTime(maxTime);

        while (concoredocker.getSimtime() < maxTime) {
            concoredocker.ReadResult readResult = concoredocker.read(1, "u", INIT_SIMTIME_U);
            List<Object> u = readResult.data;

            double u0 = 0.0;
            if (!u.isEmpty()) {
                u0 = toDouble(u.get(0));
            }

            double ym0 = u0 + 0.01;
            List<Object> ym = new ArrayList<>();
            ym.add(ym0);

            System.out.println(concoredocker.getSimtime() + ". u=" + u + " ym=" + ym);
            concoredocker.write(1, "ym", ym, 1);
        }
    }
}
