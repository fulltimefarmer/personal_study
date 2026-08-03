# 题目 9：简化 JSON 解析器

## 题目描述

实现一个**简化版 JSON 解析器**，能将 JSON 字符串解析为 Java 对象（Map、List、String、Number、Boolean、null），并能将 Java 对象序列化回 JSON 字符串。

要求实现：

- `Object parse(String json)` —— 将 JSON 字符串解析为对应的 Java 对象。
- `String stringify(Object obj)` —— 将 Java 对象序列化为 JSON 字符串。

支持的 JSON 数据类型：
- **对象** `{"key": "value"}` → `Map<String, Object>`
- **数组** `[1, 2, 3]` → `List<Object>`
- **字符串** `"hello"` → `String`
- **数字**（整数和浮点数） → `Long` 或 `Double`
- **布尔值** `true` / `false` → `Boolean`
- **null** → `null`
- **嵌套**：对象和数组可以任意嵌套。

## 示例

```java
String json = "{\"name\":\"Alice\",\"age\":30,\"address\":{\"city\":\"NYC\"},\"tags\":[\"dev\",\"java\"]}";

Object result = parser.parse(json);
// result -> Map {
//   "name"   -> "Alice",
//   "age"    -> 30,
//   "address"-> Map {"city" -> "NYC"},
//   "tags"   -> List ["dev", "java"]
// }

String back = parser.stringify(result);
// back -> {"name":"Alice","age":30,"address":{"city":"NYC"},"tags":["dev","java"]}
```

## 解题思路

### 1. 解析器整体架构

```
                    ┌────────────────┐
                    │  JSON 字符串    │
                    └───────┬────────┘
                            ▼
                    ┌────────────────┐
                    │   Tokenizer    │  词法分析
                    │  (Lexer)       │  字符流 → Token 流
                    └───────┬────────┘
                            ▼
                    ┌────────────────┐
                    │    Parser      │  语法分析
                    │  (递归下降)     │  Token 流 → AST/对象
                    └───────┬────────┘
                            ▼
                    ┌────────────────┐
                    │  Map/List/...  │  Java 对象
                    └────────────────┘
```

### 2. 词法分析（Tokenizer）

将原始字符流转换为有意义的 Token：

```java
enum TokenType {
    LEFT_BRACE,    // {
    RIGHT_BRACE,   // }
    LEFT_BRACKET,  // [
    RIGHT_BRACKET, // ]
    COLON,         // :
    COMMA,         // ,
    STRING,        // "hello"
    NUMBER,        // 123, 3.14, -5
    BOOLEAN,       // true, false
    NULL           // null
}
```

词法分析流程：

```
输入: {"name":"Alice"}
     ↓ 跳过空白字符
Token{ '{' }
     ↓ 读取字符串
Token{ STRING, "name" }
     ↓
Token{ ':' }
     ↓ 读取字符串
Token{ STRING, "Alice" }
     ↓
Token{ '}' }
```

关键实现细节：
- 字符串解析：读取引号之间的内容，处理 `\"`, `\\`, `\n` 等转义字符。
- 数字解析：区分整数和浮点数，处理负号和科学计数法（可选）。
- 布尔/null 解析：匹配关键字 `true`/`false`/`null`。

### 3. 语法分析（递归下降解析器）

采用**递归下降**方法，每种 JSON 类型对应一个解析方法：

```java
Object parseValue() {
    Token token = peek();
    switch (token.type) {
        case LEFT_BRACE:  return parseObject();
        case LEFT_BRACKET: return parseArray();
        case STRING:      return parseString();
        case NUMBER:      return parseNumber();
        case BOOLEAN:     return parseBoolean();
        case NULL:        return parseNull();
        default:          throw parseError("Unexpected token");
    }
}

Map<String, Object> parseObject() {
    Map<String, Object> map = new LinkedHashMap<>();
    consume(LEFT_BRACE);
    while (peek().type != RIGHT_BRACE) {
        String key = parseString();
        consume(COLON);
        Object value = parseValue();
        map.put(key, value);
        if (peek().type == COMMA) consume(COMMA); else break;
    }
    consume(RIGHT_BRACE);
    return map;
}
```

### 4. 序列化（Stringify）

反向将 Java 对象转为 JSON 字符串：

```java
String stringify(Object obj) {
    if (obj == null) return "null";
    if (obj instanceof String) return "\"" + escape((String) obj) + "\"";
    if (obj instanceof Number || obj instanceof Boolean) return obj.toString();
    if (obj instanceof Map) return stringifyObject((Map) obj);
    if (obj instanceof List) return stringifyArray((List) obj);
    throw new IllegalArgumentException("Unsupported type: " + obj.getClass());
}
```

### 5. 错误处理

生产级解析器需要友好的错误信息：

```java
class JsonParseException extends RuntimeException {
    private final int position;
    private final int line;
    private final int column;

    // 清晰的错误消息: "Unexpected token at line 3, column 15: expected '}' but got ']'"
}
```

### 6. 复杂度分析

- **时间复杂度**：O(n)，n 为输入字符串长度（单遍扫描）。
- **空间复杂度**：O(d + k)，d 为嵌套深度，k 为 key/value 数量。

## 考察维度

- **算法基础**：递归下降解析、词法/语法分析分离。
- **代码结构**：清晰的状态机/递归设计，错误处理和位置追踪。
- **生产实践**：转义字符处理、数值精度、Unicode 支持、可扩展性。
- **技术深度**：编译原理基础（词法分析 → 语法分析 → 语义动作）。
