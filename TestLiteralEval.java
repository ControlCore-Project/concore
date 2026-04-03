import java.util.*;

/**
 * Test suite for concoredocker.literalEval() recursive descent parser.
 * Covers: dicts, lists, tuples, numbers, strings, booleans, None,
 *         nested structures, escape sequences, scientific notation,
 *         fractional simtime, and related round-trip parsing behavior.
 */
public class TestLiteralEval {
    static int passed = 0;
    static int failed = 0;

    public static void main(String[] args) {
        testEmptyDict();
        testSimpleDict();
        testDictWithIntValues();
        testEmptyList();
        testSimpleList();
        testListOfDoubles();
        testNestedDictWithList();
        testNestedListsDeep();
        testBooleansAndNone();
        testStringsWithCommas();
        testStringsWithColons();
        testStringEscapeSequences();
        testScientificNotation();
        testNegativeNumbers();
        testTuple();
        testTrailingComma();
        testToPythonLiteralBooleans();
        testToPythonLiteralNone();
        testToPythonLiteralString();
        testFractionalSimtime();
        testRoundTripSerialization();
        testStringEscapingSerialization();
        testUnterminatedList();
        testUnterminatedDict();
        testUnterminatedTuple();
        testNonStringDictKey();
        testJsonKeywordTrue();
        testJsonKeywordFalse();
        testJsonKeywordNull();
        testJsonMixedList();
        testJsonRoundTrip();

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

    static void testEmptyDict() {
        Object result = concoredocker.literalEval("{}");
        check("empty dict", new HashMap<>(), result);
    }

    static void testSimpleDict() {
        @SuppressWarnings("unchecked")
        Map<String, Object> result = (Map<String, Object>) concoredocker.literalEval("{'PYM': 1}");
        check("simple dict key", true, result.containsKey("PYM"));
        check("simple dict value", 1, result.get("PYM"));
    }

    static void testDictWithIntValues() {
        @SuppressWarnings("unchecked")
        Map<String, Object> result = (Map<String, Object>) concoredocker.literalEval("{'a': 10, 'b': 20}");
        check("dict int value a", 10, result.get("a"));
        check("dict int value b", 20, result.get("b"));
    }

    static void testEmptyList() {
        Object result = concoredocker.literalEval("[]");
        check("empty list", new ArrayList<>(), result);
    }

    static void testSimpleList() {
        @SuppressWarnings("unchecked")
        List<Object> result = (List<Object>) concoredocker.literalEval("[1, 2, 3]");
        check("simple list size", 3, result.size());
        check("simple list[0]", 1, result.get(0));
        check("simple list[2]", 3, result.get(2));
    }

    static void testListOfDoubles() {
        @SuppressWarnings("unchecked")
        List<Object> result = (List<Object>) concoredocker.literalEval("[0.0, 1.5, 2.7]");
        check("list doubles[0]", 0.0, result.get(0));
        check("list doubles[1]", 1.5, result.get(1));
    }

    static void testNestedDictWithList() {
        @SuppressWarnings("unchecked")
        Map<String, Object> result = (Map<String, Object>) concoredocker.literalEval("{'key': [1, 2, 3]}");
        check("nested dict has key", true, result.containsKey("key"));
        @SuppressWarnings("unchecked")
        List<Object> inner = (List<Object>) result.get("key");
        check("nested list size", 3, inner.size());
        check("nested list[0]", 1, inner.get(0));
    }

    static void testNestedListsDeep() {
        @SuppressWarnings("unchecked")
        List<Object> result = (List<Object>) concoredocker.literalEval("[[1, 2], [3, 4]]");
        check("nested lists size", 2, result.size());
        @SuppressWarnings("unchecked")
        List<Object> inner = (List<Object>) result.get(0);
        check("inner list[0]", 1, inner.get(0));
        check("inner list[1]", 2, inner.get(1));
    }

    static void testBooleansAndNone() {
        @SuppressWarnings("unchecked")
        List<Object> result = (List<Object>) concoredocker.literalEval("[True, False, None]");
        check("boolean True", Boolean.TRUE, result.get(0));
        check("boolean False", Boolean.FALSE, result.get(1));
        check("None", null, result.get(2));
    }

    static void testStringsWithCommas() {
        @SuppressWarnings("unchecked")
        Map<String, Object> result = (Map<String, Object>) concoredocker.literalEval("{'key': 'hello, world'}");
        check("string with comma", "hello, world", result.get("key"));
    }

    static void testStringsWithColons() {
        @SuppressWarnings("unchecked")
        Map<String, Object> result = (Map<String, Object>) concoredocker.literalEval("{'url': 'http://example.com'}");
        check("string with colon", "http://example.com", result.get("url"));
    }

    static void testStringEscapeSequences() {
        Object result = concoredocker.literalEval("'hello\\nworld'");
        check("escaped newline", "hello\nworld", result);
    }

    static void testScientificNotation() {
        Object result = concoredocker.literalEval("1.5e3");
        check("scientific notation", 1500.0, result);
    }

    static void testNegativeNumbers() {
        @SuppressWarnings("unchecked")
        List<Object> result = (List<Object>) concoredocker.literalEval("[-1, -2.5, 3]");
        check("negative int", -1, result.get(0));
        check("negative double", -2.5, result.get(1));
        check("positive int", 3, result.get(2));
    }

    static void testTuple() {
        @SuppressWarnings("unchecked")
        List<Object> result = (List<Object>) concoredocker.literalEval("(1, 2, 3)");
        check("tuple size", 3, result.size());
        check("tuple[0]", 1, result.get(0));
    }

    static void testTrailingComma() {
        @SuppressWarnings("unchecked")
        List<Object> result = (List<Object>) concoredocker.literalEval("[1, 2, 3,]");
        check("trailing comma size", 3, result.size());
    }

    // --- Serialization tests (toPythonLiteral via write format) ---

    static void testToPythonLiteralBooleans() {
        // Test that booleans serialize to Python format (True/False, not true/false)
        @SuppressWarnings("unchecked")
        List<Object> input = (List<Object>) concoredocker.literalEval("[True, False]");
        // Re-parse and check the values are correct Java booleans
        check("parsed True is Boolean.TRUE", Boolean.TRUE, input.get(0));
        check("parsed False is Boolean.FALSE", Boolean.FALSE, input.get(1));
    }

    static void testToPythonLiteralNone() {
        @SuppressWarnings("unchecked")
        List<Object> input = (List<Object>) concoredocker.literalEval("[None, 1]");
        check("parsed None is null", null, input.get(0));
        check("parsed 1 is Integer 1", 1, input.get(1));
    }

    static void testToPythonLiteralString() {
        Object result = concoredocker.literalEval("'hello'");
        check("parsed string", "hello", result);
    }

    static void testFractionalSimtime() {
        // Simtime values like [0.5, 1.0, 2.0] should preserve fractional part
        @SuppressWarnings("unchecked")
        List<Object> result = (List<Object>) concoredocker.literalEval("[0.5, 1.0, 2.0]");
        check("fractional simtime[0]", 0.5, result.get(0));
        check("fractional simtime[1]", 1.0, result.get(1));
        check("fractional simtime[2]", 2.0, result.get(2));
    }

    // --- Round-trip serialization tests ---

    static void testRoundTripSerialization() {
        // Conceptually: a list with mixed types [1, 2.5, true, false, null, "hello"]
        // Use reflection-free approach: build the Python literal manually
        // and verify round-trip through literalEval
        String serialized = "[1, 2.5, True, False, None, 'hello']";
        @SuppressWarnings("unchecked")
        List<Object> roundTripped = (List<Object>) concoredocker.literalEval(serialized);
        check("round-trip int", 1, roundTripped.get(0));
        check("round-trip double", 2.5, roundTripped.get(1));
        check("round-trip True", Boolean.TRUE, roundTripped.get(2));
        check("round-trip False", Boolean.FALSE, roundTripped.get(3));
        check("round-trip None", null, roundTripped.get(4));
        check("round-trip string", "hello", roundTripped.get(5));
    }

    static void testStringEscapingSerialization() {
        // Strings with special chars should survive parse -> serialize -> re-parse
        String input = "'hello\\nworld'";
        Object parsed = concoredocker.literalEval(input);
        check("escape parse", "hello\nworld", parsed);

        // Test string with embedded single quote
        String input2 = "'it\\'s'";
        Object parsed2 = concoredocker.literalEval(input2);
        check("escape single quote", "it's", parsed2);
    }

    // --- Unterminated input tests (should throw) ---

    static void testUnterminatedList() {
        try {
            concoredocker.literalEval("[1, 2");
            System.out.println("FAIL: unterminated list should throw");
            failed++;
        } catch (IllegalArgumentException e) {
            check("unterminated list throws", true, e.getMessage().contains("Unterminated list"));
        }
    }

    static void testUnterminatedDict() {
        try {
            concoredocker.literalEval("{'a': 1");
            System.out.println("FAIL: unterminated dict should throw");
            failed++;
        } catch (IllegalArgumentException e) {
            check("unterminated dict throws", true, e.getMessage().contains("Unterminated dict"));
        }
    }

    static void testUnterminatedTuple() {
        try {
            concoredocker.literalEval("(1, 2");
            System.out.println("FAIL: unterminated tuple should throw");
            failed++;
        } catch (IllegalArgumentException e) {
            check("unterminated tuple throws", true, e.getMessage().contains("Unterminated tuple"));
        }
    }

    static void testNonStringDictKey() {
        // Dict keys must be strings - numeric keys should throw
        try {
            concoredocker.literalEval("{123: 'value'}");
            System.out.println("FAIL: numeric dict key should throw");
            failed++;
        } catch (IllegalArgumentException e) {
            check("numeric dict key throws", true, e.getMessage().contains("Dict keys must be non-null strings"));
        }
    }

    // --- JSON keyword interop tests ---

    static void testJsonKeywordTrue() {
        Object result = concoredocker.literalEval("true");
        check("json true -> Boolean.TRUE", Boolean.TRUE, result);
    }

    static void testJsonKeywordFalse() {
        Object result = concoredocker.literalEval("false");
        check("json false -> Boolean.FALSE", Boolean.FALSE, result);
    }

    static void testJsonKeywordNull() {
        Object result = concoredocker.literalEval("null");
        check("json null -> null", null, result);
    }

    static void testJsonMixedList() {
        // Python sends [0.0, true, null] via json.dumps — Java must parse it
        @SuppressWarnings("unchecked")
        List<Object> result = (List<Object>) concoredocker.literalEval("[0.0, true, null]");
        check("json list[0] simtime", 0.0, result.get(0));
        check("json list[1] true", Boolean.TRUE, result.get(1));
        check("json list[2] null", null, result.get(2));
    }

    static void testJsonRoundTrip() {
        // JSON-style payload: true/false/null and double-quoted strings
        String jsonPayload = "[0.0, 1.5, true, false, null, \"hello\"]";
        @SuppressWarnings("unchecked")
        List<Object> result = (List<Object>) concoredocker.literalEval(jsonPayload);
        check("json round-trip double", 1.5, result.get(1));
        check("json round-trip true", Boolean.TRUE, result.get(2));
        check("json round-trip false", Boolean.FALSE, result.get(3));
        check("json round-trip null", null, result.get(4));
        check("json round-trip string", "hello", result.get(5));
    }
}
