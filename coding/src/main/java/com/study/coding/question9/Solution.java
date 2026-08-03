package com.study.coding.question9;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * A simplified JSON parser/serializer that handles objects, arrays, strings,
 * numbers, booleans, null, and arbitrary nesting.
 *
 * <p>Implements a recursive-descent parser with a hand-rolled tokenizer.
 * Does not use any external JSON libraries.
 */
public class Solution {

    // 【问题求解】可变解析状态（pos, json）——有状态递归下降解析的经典模式
    private String json;
    private int pos;

    /**
     * Parses a JSON string into corresponding Java objects.
     *
     * @param json the JSON string to parse
     * @return the parsed object (Map, List, String, Long, Double, Boolean, or null)
     * @throws JsonParseException on malformed JSON
     */
    // 【生产实践】parse 入口完整校验：null 输入、空串、尾随字符——防御式编程
    public Object parse(String json) {
        if (json == null) {
            throw new JsonParseException("Input json must not be null", 0);
        }
        this.pos = 0;
        this.json = json;
        skipWhitespace();
        if (pos >= json.length()) {
            throw new JsonParseException("Empty JSON string", pos);
        }
        Object result = parseValue();
        skipWhitespace();
        if (pos < json.length()) {
            throw new JsonParseException("Trailing characters after JSON value", pos);
        }
        return result;
    }

    /**
     * Serializes a Java object into a JSON string.
     *
     * @param obj the object to serialize
     * @return the JSON string representation
     * @throws IllegalArgumentException if the object type is not supported
     */
    // 【技术深度】pattern matching instanceof (Java 16+) + 递归——简洁的类型分发与嵌套序列化
    public String stringify(Object obj) {
        if (obj == null) {
            return "null";
        }
        if (obj instanceof String s) {
            return "\"" + escapeJson(s) + "\"";
        }
        if (obj instanceof Boolean || obj instanceof Number) {
            return obj.toString();
        }
        if (obj instanceof Map<?, ?> m) {
            return stringifyMap(m);
        }
        if (obj instanceof List<?> l) {
            return stringifyList(l);
        }
        throw new IllegalArgumentException("Unsupported type: " + obj.getClass().getName());
    }

    // ──────────────────────────────────────────────
    // Parser
    // ──────────────────────────────────────────────

    // 【问题求解】switch 首字符分发——基于 JSON 首字符确定性跳转到对应解析器
    private Object parseValue() {
        skipWhitespace();
        char c = current();
        switch (c) {
            case '{': return parseObject();
            case '[': return parseArray();
            case '"': return parseString();
            case 't': case 'f': return parseBoolean();
            case 'n': return parseNull();
            default:
                if (c == '-' || Character.isDigit(c)) {
                    return parseNumber();
                }
                throw new JsonParseException("Unexpected character: " + c, pos);
        }
    }

    // 【生产实践】LinkedHashMap 保持插入顺序——JSON 对象键顺序在往返时不丢失
    private Map<String, Object> parseObject() {
        consume('{');
        Map<String, Object> map = new LinkedHashMap<>();
        skipWhitespace();
        if (current() == '}') {
            pos++;
            return map;
        }
        while (true) {
            skipWhitespace();
            String key = parseString();
            skipWhitespace();
            consume(':');
            skipWhitespace();
            Object value = parseValue();
            map.put(key, value);
            skipWhitespace();
            if (current() == ',') {
                pos++;
            } else if (current() == '}') {
                pos++;
                return map;
            } else {
                throw new JsonParseException("Expected ',' or '}' in object", pos);
            }
        }
    }

    private List<Object> parseArray() {
        consume('[');
        List<Object> list = new ArrayList<>();
        skipWhitespace();
        if (current() == ']') {
            pos++;
            return list;
        }
        while (true) {
            skipWhitespace();
            list.add(parseValue());
            skipWhitespace();
            if (current() == ',') {
                pos++;
            } else if (current() == ']') {
                pos++;
                return list;
            } else {
                throw new JsonParseException("Expected ',' or ']' in array", pos);
            }
        }
    }

    // 【技术深度】转义序列完整处理：8 种标准转义 + \\u Unicode，覆盖 JSON 规范
    private String parseString() {
        consume('"');
        StringBuilder sb = new StringBuilder();
        while (pos < json.length() && json.charAt(pos) != '"') {
            char c = json.charAt(pos);
            if (c == '\\') {
                pos++;
                if (pos >= json.length()) {
                    throw new JsonParseException("Unexpected end of input in string escape", pos);
                }
                char escaped = json.charAt(pos);
                switch (escaped) {
                    case '"':  sb.append('"');  break;
                    case '\\': sb.append('\\'); break;
                    case '/':  sb.append('/');  break;
                    case 'n':  sb.append('\n'); break;
                    case 't':  sb.append('\t'); break;
                    case 'r':  sb.append('\r'); break;
                    case 'b':  sb.append('\b'); break;
                    case 'f':  sb.append('\f'); break;
                    case 'u':  sb.append(parseUnicode()); continue;
                    default:
                        throw new JsonParseException("Invalid escape sequence: \\" + escaped, pos);
                }
            } else {
                sb.append(c);
            }
            pos++;
        }
        if (pos >= json.length()) {
            throw new JsonParseException("Unterminated string", pos);
        }
        pos++; // skip closing quote
        return sb.toString();
    }

    private char parseUnicode() {
        if (pos + 4 >= json.length()) {
            throw new JsonParseException("Incomplete unicode escape", pos);
        }
        String hex = json.substring(pos + 1, pos + 5);
        try {
            char result = (char) Integer.parseInt(hex, 16);
            pos += 4;
            return result;
        } catch (NumberFormatException e) {
            throw new JsonParseException("Invalid unicode escape: \\u" + hex, pos);
        }
    }

    // 【技术深度】整数 vs 浮点自动检测 + Long 溢出兜底——精确类型推断
    private Number parseNumber() {
        int start = pos;
        if (current() == '-') {
            pos++;
        }
        while (pos < json.length() && Character.isDigit(json.charAt(pos))) {
            pos++;
        }
        boolean isDouble = false;
        if (pos < json.length() && json.charAt(pos) == '.') {
            isDouble = true;
            pos++;
            while (pos < json.length() && Character.isDigit(json.charAt(pos))) {
                pos++;
            }
        }
        if (pos < json.length() && (json.charAt(pos) == 'e' || json.charAt(pos) == 'E')) {
            isDouble = true;
            pos++;
            if (pos < json.length() && (json.charAt(pos) == '+' || json.charAt(pos) == '-')) {
                pos++;
            }
            while (pos < json.length() && Character.isDigit(json.charAt(pos))) {
                pos++;
            }
        }
        String numberStr = json.substring(start, pos);
        if (isDouble) {
            return Double.parseDouble(numberStr);
        }
        try {
            return Long.parseLong(numberStr);
        } catch (NumberFormatException e) {
            return Double.parseDouble(numberStr);
        }
    }

    private Boolean parseBoolean() {
        if (matchKeyword("true")) {
            return Boolean.TRUE;
        }
        if (matchKeyword("false")) {
            return Boolean.FALSE;
        }
        throw new JsonParseException("Invalid boolean literal", pos);
    }

    private Object parseNull() {
        if (matchKeyword("null")) {
            return null;
        }
        throw new JsonParseException("Invalid null literal", pos);
    }

    private boolean matchKeyword(String keyword) {
        if (json.startsWith(keyword, pos)) {
            pos += keyword.length();
            return true;
        }
        return false;
    }

    // ──────────────────────────────────────────────
    // Serializer
    // ──────────────────────────────────────────────

    private String stringifyMap(Map<?, ?> map) {
        StringBuilder sb = new StringBuilder("{");
        boolean first = true;
        for (Map.Entry<?, ?> entry : map.entrySet()) {
            if (!first) sb.append(",");
            sb.append(stringify(entry.getKey()));
            sb.append(":");
            sb.append(stringify(entry.getValue()));
            first = false;
        }
        sb.append("}");
        return sb.toString();
    }

    private String stringifyList(List<?> list) {
        StringBuilder sb = new StringBuilder("[");
        boolean first = true;
        for (Object item : list) {
            if (!first) sb.append(",");
            sb.append(stringify(item));
            first = false;
        }
        sb.append("]");
        return sb.toString();
    }

    private String escapeJson(String s) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            switch (c) {
                case '"':  sb.append("\\\""); break;
                case '\\': sb.append("\\\\"); break;
                case '\n': sb.append("\\n");  break;
                case '\t': sb.append("\\t");  break;
                case '\r': sb.append("\\r");  break;
                case '\b': sb.append("\\b");  break;
                case '\f': sb.append("\\f");  break;
                default:   sb.append(c);
            }
        }
        return sb.toString();
    }

    // ──────────────────────────────────────────────
    // Helpers
    // ──────────────────────────────────────────────

    // 【代码质量】current() 哨兵 '\0' 处理越界——统一字符读取接口，避免重复越界检查
    private char current() {
        return pos < json.length() ? json.charAt(pos) : '\0';
    }

    private void consume(char expected) {
        if (current() != expected) {
            throw new JsonParseException(
                    "Expected '" + expected + "' but got '" + current() + "'", pos);
        }
        pos++;
    }

    private void skipWhitespace() {
        while (pos < json.length() && Character.isWhitespace(json.charAt(pos))) {
            pos++;
        }
    }

    // ──────────────────────────────────────────────
    // Exception
    // ──────────────────────────────────────────────

    // 【生产实践】自定义异常携带位置信息——快速定位 JSON 错误位置，提升可调试性
    public static class JsonParseException extends RuntimeException {
        public final int position;

        JsonParseException(String message, int position) {
            super(message + " at position " + position);
            this.position = position;
        }
    }
}
