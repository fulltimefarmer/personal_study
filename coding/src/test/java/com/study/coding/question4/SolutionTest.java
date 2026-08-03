package com.study.coding.question4;

import org.junit.jupiter.api.Test;
import java.util.List;
import static org.junit.jupiter.api.Assertions.*;

class SolutionTest {

    private final Solution solution = new Solution();

    @Test
    void shouldJustifyExampleCase() {
        String[] words = {"This", "is", "an", "example", "of", "text", "justification."};
        List<String> result = solution.fullJustify(words, 16);

        assertEquals(3, result.size());
        assertEquals("This    is    an", result.get(0));
        assertEquals("example  of text", result.get(1));
        assertEquals("justification.  ", result.get(2));

        // 【代码质量】全面断言：验证所有行长度等于 maxWidth
        for (String line : result) {
            assertEquals(16, line.length());
        }
    }

    @Test
    void shouldJustifySingleWord() {
        List<String> result = solution.fullJustify(new String[]{"hello"}, 10);
        assertEquals(1, result.size());
        assertEquals("hello     ", result.get(0));
        assertEquals(10, result.get(0).length());
    }

    @Test
    void shouldLeftJustifyLastLine() {
        String[] words = {"What", "must", "be", "acknowledgment", "shall", "be"};
        List<String> result = solution.fullJustify(words, 16);

        assertEquals(3, result.size());
        // Last line should be left-justified
        assertEquals("shall be        ", result.get(2));
    }

    @Test
    void shouldHandleExactFit() {
        String[] words = {"abc", "de", "f"};
        List<String> result = solution.fullJustify(words, 5);
        assertEquals(2, result.size());
        assertEquals("abc  ", result.get(0));
        assertEquals("de f ", result.get(1));
    }

    @Test
    void shouldDistributeExtraSpacesToLeftFirst() {
        String[] words = {"a", "b", "c", "d", "e"};
        List<String> result = solution.fullJustify(words, 8);

        assertEquals(2, result.size());
        // Line "a b c d" with 4 spaces total across 3 gaps: 1+1 from base, remainder 1 goes to first gap
        assertEquals("a  b c d", result.get(0));
        assertEquals("e       ", result.get(1));
        assertEquals(8, result.get(0).length());
        assertEquals(8, result.get(1).length());
    }

    // 【代码质量】边界测试：空输入返回空列表
    @Test
    void shouldReturnEmptyListForEmptyInput() {
        List<String> result = solution.fullJustify(new String[]{}, 5);
        assertTrue(result.isEmpty());
    }

    // 【代码质量】参数校验测试：覆盖 null 和非法 maxWidth
    @Test
    void shouldRejectNullWordsArray() {
        assertThrows(NullPointerException.class, () -> solution.fullJustify(null, 5));
    }

    @Test
    void shouldRejectInvalidMaxWidth() {
        assertThrows(IllegalArgumentException.class, () -> solution.fullJustify(new String[]{"a"}, 0));
        assertThrows(IllegalArgumentException.class, () -> solution.fullJustify(new String[]{"a"}, -1));
    }

    // 【代码质量】防御性测试：验证返回值不可修改
    @Test
    void shouldReturnUnmodifiableList() {
        List<String> result = solution.fullJustify(new String[]{"hello"}, 10);
        assertThrows(UnsupportedOperationException.class, () -> result.add("extra"));
    }
}
