package com.study.coding.question9;

import org.junit.jupiter.api.Test;
import java.util.List;
import java.util.Map;
import static org.junit.jupiter.api.Assertions.*;

class SolutionTest {

    private final Solution parser = new Solution();

    // ──────────────────────────────────────────────
    // Parse tests
    // ──────────────────────────────────────────────

    // 【技术深度】instanceof 类型断言 + 转换：确保解析结果类型正确再取值
    @Test
    void shouldParseSimpleObject() {
        Object result = parser.parse("{\"name\":\"Alice\"}");

        assertTrue(result instanceof Map);
        Map<?, ?> map = (Map<?, ?>) result;
        assertEquals("Alice", map.get("name"));
    }

    @Test
    void shouldParseNestedObject() {
        Object result = parser.parse(
                "{\"person\":{\"name\":\"Alice\",\"age\":30}}");

        assertTrue(result instanceof Map);
        Map<?, ?> outer = (Map<?, ?>) result;
        Map<?, ?> inner = (Map<?, ?>) outer.get("person");
        assertEquals("Alice", inner.get("name"));
        assertEquals(30L, inner.get("age"));
    }

    // 【代码质量】List 类型断言后逐元素校验：确保数组元素类型与数量正确
    @Test
    void shouldParseArray() {
        Object result = parser.parse("[1,2,3]");

        assertTrue(result instanceof List);
        List<?> list = (List<?>) result;
        assertEquals(3, list.size());
        assertEquals(1L, list.get(0));
        assertEquals(2L, list.get(1));
        assertEquals(3L, list.get(2));
    }

    @Test
    void shouldParseNestedArrayInObject() {
        Object result = parser.parse("{\"tags\":[\"dev\",\"java\"]}");

        Map<?, ?> map = (Map<?, ?>) result;
        List<?> tags = (List<?>) map.get("tags");
        assertEquals("dev", tags.get(0));
        assertEquals("java", tags.get(1));
    }

    // 【技术深度】boolean 与 null 值往返测试：覆盖 JSON 三种字面量类型
    @Test
    void shouldParseBooleanAndNull() {
        Object result = parser.parse("{\"active\":true,\"extra\":null,\"deleted\":false}");

        Map<?, ?> map = (Map<?, ?>) result;
        assertEquals(true, map.get("active"));
        assertNull(map.get("extra"));
        assertEquals(false, map.get("deleted"));
    }

    @Test
    void shouldParseFloatingPointNumbers() {
        Object result = parser.parse("{\"price\":3.14}");

        Map<?, ?> map = (Map<?, ?>) result;
        assertEquals(3.14, map.get("price"));
    }

    @Test
    void shouldParseNegativeNumbers() {
        Object result = parser.parse("[-1, -3.5]");

        List<?> list = (List<?>) result;
        assertEquals(-1L, list.get(0));
        assertEquals(-3.5, list.get(1));
    }

    @Test
    void shouldParseEmptyObjectAndArray() {
        assertEquals(0, ((Map<?, ?>) parser.parse("{}")).size());
        assertEquals(0, ((List<?>) parser.parse("[]")).size());
    }

    // 【技术深度】转义字符处理：覆盖换行符 \n 与转义引号 \" 的正反序列化
    @Test
    void shouldParseStringWithEscapes() {
        Object result = parser.parse("{\"msg\":\"hello\\nworld\\\"quoted\\\"\"}");

        Map<?, ?> map = (Map<?, ?>) result;
        assertEquals("hello\nworld\"quoted\"", map.get("msg"));
    }

    // 【生产实践】非法 JSON 与 null 输入拒收：防御性解析，杜绝静默失败
    @Test
    void shouldThrowOnMalformedJson() {
        assertThrows(Solution.JsonParseException.class,
                () -> parser.parse("{broken"));
        assertThrows(Solution.JsonParseException.class,
                () -> parser.parse("{\"key\":"));
    }

    @Test
    void shouldThrowOnNullInput() {
        assertThrows(Solution.JsonParseException.class,
                () -> parser.parse(null));
    }

    // ──────────────────────────────────────────────
    // Stringify tests
    // ──────────────────────────────────────────────

    // 【代码质量】parse → stringify → parse 往返幂等测试：验证序列化与反序列化的一致性
    @Test
    void shouldStringifyAndParseRoundTrip() {
        String original = "{\"name\":\"Alice\",\"age\":30,\"active\":true,\"tags\":[\"dev\",\"java\"]}";
        Object parsed = parser.parse(original);
        String serialized = parser.stringify(parsed);
        Object reparsed = parser.parse(serialized);

        assertEquals(parsed, reparsed);
    }

    @Test
    void shouldStringifyNull() {
        assertEquals("null", parser.stringify(null));
    }

    @Test
    void shouldStringifySimpleTypes() {
        assertEquals("\"hello\"", parser.stringify("hello"));
        assertEquals("42", parser.stringify(42L));
        assertEquals("true", parser.stringify(true));
        assertEquals("false", parser.stringify(false));
    }

    @Test
    void shouldStringifyNestedStructures() {
        Map<String, Object> inner = new java.util.LinkedHashMap<>();
        inner.put("city", "NYC");
        Map<String, Object> outer = new java.util.LinkedHashMap<>();
        outer.put("address", inner);

        String json = parser.stringify(outer);
        assertTrue(json.contains("\"city\":\"NYC\""));
        assertTrue(json.startsWith("{"));
        assertTrue(json.endsWith("}"));
    }
}
