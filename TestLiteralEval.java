import java.util.List;
import java.util.Map;
import java.lang.reflect.Method;
import java.lang.reflect.Field;

/**
 * Test cases for the literalEval implementation in concoredocker.
 * This verifies the fix for GitHub Issue #228.
 */
public class TestLiteralEval {
    private static int passed = 0;
    private static int failed = 0;

    public static void main(String[] args) throws Exception {
        System.out.println("Testing literalEval implementation...\n");

        // Get the private literalEval method via reflection
        Method literalEval = concoredocker.class.getDeclaredMethod("literalEval", String.class);
        literalEval.setAccessible(true);

        // Get toPythonLiteral method for serialization tests
        Method toPythonLiteral = concoredocker.class.getDeclaredMethod("toPythonLiteral", Object.class);
        toPythonLiteral.setAccessible(true);

        // Test 1: Simple dictionary (port file format)
        testDict(literalEval, "{'PYM': 1}", "PYM", 1);
        
        // Test 2: Dictionary with multiple keys
        testDict(literalEval, "{'CU': 1, 'PYM': 2}", "CU", 1);
        
        // Test 3: Simple list (data format)
        testList(literalEval, "[0.0, 0.0]", 2);
        
        // Test 4: List with mixed types
        testList(literalEval, "[0, 1.5, 2.3]", 3);
        
        // Test 5: Simple integer (maxtime format)
        testNumber(literalEval, "100", 100);
        
        // Test 6: Float number
        testNumber(literalEval, "3.14", 3.14);
        
        // Test 7: Negative number
        testNumber(literalEval, "-42", -42);
        
        // Test 8: String value
        testString(literalEval, "'hello'", "hello");
        
        // Test 9: Double-quoted string
        testString(literalEval, "\"world\"", "world");
        
        // Test 10: Empty dictionary
        testEmptyDict(literalEval, "{}");
        
        // Test 11: Empty list
        testEmptyList(literalEval, "[]");
        
        // Test 12: Boolean True
        testBoolean(literalEval, "True", true);
        
        // Test 13: Boolean False
        testBoolean(literalEval, "False", false);
        
        // Test 14: Nested structure (dict with list value)
        testNestedDictList(literalEval, "{'values': [1, 2, 3]}");
        
        // Test 15: Scientific notation
        testNumber(literalEval, "1.5e-3", 0.0015);

        // Test 16: Python literal serialization - Boolean
        testSerialization(toPythonLiteral, Boolean.TRUE, "True");
        
        // Test 17: Python literal serialization - Boolean False
        testSerialization(toPythonLiteral, Boolean.FALSE, "False");
        
        // Test 18: Python literal serialization - null
        testSerialization(toPythonLiteral, null, "None");
        
        // Test 19: Python literal serialization - String with quotes
        testSerialization(toPythonLiteral, "hello", "'hello'");
        
        // Test 20: Fractional simtime preserved (double)
        testFractionalSimtime(literalEval);

        System.out.println("\n========================================");
        System.out.println("Results: " + passed + " passed, " + failed + " failed");
        System.out.println("========================================");
        
        if (failed > 0) {
            System.exit(1);
        }
    }

    @SuppressWarnings("unchecked")
    private static void testDict(Method literalEval, String input, String key, Object expectedValue) {
        try {
            Object result = literalEval.invoke(null, input);
            if (result instanceof Map) {
                Map<String, Object> map = (Map<String, Object>) result;
                if (map.containsKey(key)) {
                    Object actual = map.get(key);
                    if (actual instanceof Number && expectedValue instanceof Number) {
                        if (((Number) actual).doubleValue() == ((Number) expectedValue).doubleValue()) {
                            pass("Dict parse: " + input);
                            return;
                        }
                    } else if (actual.equals(expectedValue)) {
                        pass("Dict parse: " + input);
                        return;
                    }
                }
            }
            fail("Dict parse: " + input, "Expected key '" + key + "' = " + expectedValue + ", got: " + result);
        } catch (Exception e) {
            fail("Dict parse: " + input, e.getMessage());
        }
    }

    private static void testList(Method literalEval, String input, int expectedSize) {
        try {
            Object result = literalEval.invoke(null, input);
            if (result instanceof List) {
                List<?> list = (List<?>) result;
                if (list.size() == expectedSize) {
                    pass("List parse: " + input + " (size=" + expectedSize + ")");
                    return;
                }
                fail("List parse: " + input, "Expected size " + expectedSize + ", got " + list.size());
            } else {
                fail("List parse: " + input, "Expected List, got " + result.getClass().getSimpleName());
            }
        } catch (Exception e) {
            fail("List parse: " + input, e.getMessage());
        }
    }

    private static void testNumber(Method literalEval, String input, double expectedValue) {
        try {
            Object result = literalEval.invoke(null, input);
            if (result instanceof Number) {
                double actual = ((Number) result).doubleValue();
                if (Math.abs(actual - expectedValue) < 0.0001) {
                    pass("Number parse: " + input + " = " + actual);
                    return;
                }
                fail("Number parse: " + input, "Expected " + expectedValue + ", got " + actual);
            } else {
                fail("Number parse: " + input, "Expected Number, got " + result.getClass().getSimpleName());
            }
        } catch (Exception e) {
            fail("Number parse: " + input, e.getMessage());
        }
    }

    private static void testString(Method literalEval, String input, String expectedValue) {
        try {
            Object result = literalEval.invoke(null, input);
            if (result instanceof String) {
                if (result.equals(expectedValue)) {
                    pass("String parse: " + input);
                    return;
                }
                fail("String parse: " + input, "Expected '" + expectedValue + "', got '" + result + "'");
            } else {
                fail("String parse: " + input, "Expected String, got " + result.getClass().getSimpleName());
            }
        } catch (Exception e) {
            fail("String parse: " + input, e.getMessage());
        }
    }

    private static void testEmptyDict(Method literalEval, String input) {
        try {
            Object result = literalEval.invoke(null, input);
            if (result instanceof Map && ((Map<?,?>) result).isEmpty()) {
                pass("Empty dict parse: " + input);
            } else {
                fail("Empty dict parse: " + input, "Expected empty Map, got " + result);
            }
        } catch (Exception e) {
            fail("Empty dict parse: " + input, e.getMessage());
        }
    }

    private static void testEmptyList(Method literalEval, String input) {
        try {
            Object result = literalEval.invoke(null, input);
            if (result instanceof List && ((List<?>) result).isEmpty()) {
                pass("Empty list parse: " + input);
            } else {
                fail("Empty list parse: " + input, "Expected empty List, got " + result);
            }
        } catch (Exception e) {
            fail("Empty list parse: " + input, e.getMessage());
        }
    }

    private static void testBoolean(Method literalEval, String input, boolean expectedValue) {
        try {
            Object result = literalEval.invoke(null, input);
            if (result instanceof Boolean && result.equals(expectedValue)) {
                pass("Boolean parse: " + input);
            } else {
                fail("Boolean parse: " + input, "Expected " + expectedValue + ", got " + result);
            }
        } catch (Exception e) {
            fail("Boolean parse: " + input, e.getMessage());
        }
    }

    @SuppressWarnings("unchecked")
    private static void testNestedDictList(Method literalEval, String input) {
        try {
            Object result = literalEval.invoke(null, input);
            if (result instanceof Map) {
                Map<String, Object> map = (Map<String, Object>) result;
                Object values = map.get("values");
                if (values instanceof List && ((List<?>) values).size() == 3) {
                    pass("Nested dict/list parse: " + input);
                    return;
                }
            }
            fail("Nested dict/list parse: " + input, "Got: " + result);
        } catch (Exception e) {
            fail("Nested dict/list parse: " + input, e.getMessage());
        }
    }

    private static void testSerialization(Method toPythonLiteral, Object input, String expected) {
        try {
            Object result = toPythonLiteral.invoke(null, input);
            if (expected.equals(result)) {
                pass("Serialization: " + input + " -> " + result);
            } else {
                fail("Serialization: " + input, "Expected '" + expected + "', got '" + result + "'");
            }
        } catch (Exception e) {
            fail("Serialization: " + input, e.getMessage());
        }
    }

    private static void testFractionalSimtime(Method literalEval) {
        try {
            // Test that parsing a list with fractional simtime works
            Object result = literalEval.invoke(null, "[0.5, 1.2, 3.4]");
            if (result instanceof List) {
                List<?> list = (List<?>) result;
                if (list.size() == 3) {
                    Object first = list.get(0);
                    if (first instanceof Number && ((Number) first).doubleValue() == 0.5) {
                        pass("Fractional simtime: [0.5, 1.2, 3.4] preserves 0.5");
                        return;
                    }
                }
            }
            fail("Fractional simtime", "Could not verify fractional value preservation");
        } catch (Exception e) {
            fail("Fractional simtime", e.getMessage());
        }
    }

    private static void pass(String test) {
        System.out.println("[PASS] " + test);
        passed++;
    }

    private static void fail(String test, String reason) {
        System.out.println("[FAIL] " + test + " - " + reason);
        failed++;
    }
}
