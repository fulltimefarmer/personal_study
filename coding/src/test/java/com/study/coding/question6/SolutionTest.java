package com.study.coding.question6;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import static org.junit.jupiter.api.Assertions.*;

class SolutionTest {

    private final Solution solution = new Solution();

    // 【生产实践】@TempDir 提供隔离的临时目录，测试文件无需手动清理
    @Test
    void shouldReturnTopKWords(@TempDir Path tempDir) throws IOException {
        Path file = tempDir.resolve("test.txt");
        Files.writeString(file, "Hello world! Hello Java. Java, Java world.");

        List<Map.Entry<String, Integer>> result = solution.topKFrequentWords(file, 2);

        assertEquals(2, result.size());
        assertEquals("java", result.get(0).getKey());
        assertEquals(3, result.get(0).getValue());
        assertEquals("hello", result.get(1).getKey());
        assertEquals(2, result.get(1).getValue());
    }

    // 【问题求解】大小写归一化验证：所有变体归并为小写统一计数
    @Test
    void shouldNormalizeCase(@TempDir Path tempDir) throws IOException {
        Path file = tempDir.resolve("case.txt");
        Files.writeString(file, "Hello HELLO hello HeLLo");

        List<Map.Entry<String, Integer>> result = solution.topKFrequentWords(file, 1);

        assertEquals(1, result.size());
        assertEquals("hello", result.get(0).getKey());
        assertEquals(4, result.get(0).getValue());
    }

    // 【技术深度】非字母字符处理：数字、标点、连接符均被过滤，覆盖输入清洗边界
    @Test
    void shouldIgnoreNonLetters(@TempDir Path tempDir) throws IOException {
        Path file = tempDir.resolve("symbols.txt");
        Files.writeString(file, "word1, word2! word1? 123-word1.");

        List<Map.Entry<String, Integer>> result = solution.topKFrequentWords(file, 3);

        assertEquals(1, result.size());
        assertEquals("word", result.get(0).getKey());
        assertEquals(4, result.get(0).getValue());
    }

    // 【问题求解】同频按字母序排序：验证 tie-breaking 规则正确性
    @Test
    void shouldSortByAlphabetWhenFrequencyEqual(@TempDir Path tempDir) throws IOException {
        Path file = tempDir.resolve("tie.txt");
        Files.writeString(file, "apple banana");

        List<Map.Entry<String, Integer>> result = solution.topKFrequentWords(file, 2);

        assertEquals(2, result.size());
        assertEquals("apple", result.get(0).getKey());
        assertEquals("banana", result.get(1).getKey());
    }

    @Test
    void shouldHandleEmptyFile(@TempDir Path tempDir) throws IOException {
        Path file = tempDir.resolve("empty.txt");
        Files.writeString(file, "");

        List<Map.Entry<String, Integer>> result = solution.topKFrequentWords(file, 5);

        assertTrue(result.isEmpty());
    }

    @Test
    void shouldReturnAllWordsWhenKExceedsTotal(@TempDir Path tempDir) throws IOException {
        Path file = tempDir.resolve("small.txt");
        Files.writeString(file, "a b c");

        List<Map.Entry<String, Integer>> result = solution.topKFrequentWords(file, 10);

        assertEquals(3, result.size());
    }

    @Test
    void shouldRejectInvalidTopK(@TempDir Path tempDir) throws IOException {
        Path file = tempDir.resolve("test.txt");
        Files.writeString(file, "hello");

        assertThrows(IllegalArgumentException.class,
                () -> solution.topKFrequentWords(file, 0));
        assertThrows(IllegalArgumentException.class,
                () -> solution.topKFrequentWords(file, -1));
    }

    @Test
    void shouldThrowOnNullFilePath() {
        assertThrows(NullPointerException.class,
                () -> solution.topKFrequentWords(null, 5));
    }
}
