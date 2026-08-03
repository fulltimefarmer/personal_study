package com.study.coding.question6;

import java.io.BufferedReader;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.PriorityQueue;

/**
 * Memory-efficient word frequency counter for large text files.
 *
 * <p>Reads a file line-by-line using {@link BufferedReader} to keep memory bounded,
 * accumulates word counts in a {@link HashMap}, then uses a min-heap to extract
 * the top-K most frequent words.
 *
 * <p>Words are defined as contiguous sequences of letters (a-z, A-Z), normalized
 * to lowercase. All other characters act as delimiters.
 */
public class Solution {

    // 【代码质量】静态常量比较器复用，避免重复创建
    private static final Comparator<Map.Entry<String, Integer>> MIN_HEAP_COMPARATOR =
            Comparator.<Map.Entry<String, Integer>, Integer>comparing(Map.Entry::getValue)
                    .thenComparing(Map.Entry::getKey, Comparator.reverseOrder());

    /**
     * Counts word frequencies in the given file and returns the top-K entries.
     *
     * @param filePath  path to the text file
     * @param topK      number of top entries to return
     * @return unmodifiable list of top-K entries, sorted by frequency descending
     * @throws IOException              if the file cannot be read
     * @throws IllegalArgumentException if topK is not positive
     */
    public List<Map.Entry<String, Integer>> topKFrequentWords(Path filePath, int topK)
            throws IOException {
        // 【代码质量】快速失败守卫子句，前置校验输入参数
        Objects.requireNonNull(filePath, "filePath must not be null");
        if (topK <= 0) {
            throw new IllegalArgumentException("topK must be positive, got: " + topK);
        }

        // 【问题求解】分步流水线：构建频次表 → 提取 TopK 堆
        Map<String, Integer> frequencyMap = buildFrequencyMap(filePath);
        PriorityQueue<Map.Entry<String, Integer>> minHeap = buildTopKHeap(frequencyMap, topK);

        List<Map.Entry<String, Integer>> result = new ArrayList<>(minHeap);
        result.sort((a, b) -> {
            int freqCmp = b.getValue().compareTo(a.getValue());
            return freqCmp != 0 ? freqCmp : a.getKey().compareTo(b.getKey());
        });
        return Collections.unmodifiableList(result);
    }

    private Map<String, Integer> buildFrequencyMap(Path filePath) throws IOException {
        Map<String, Integer> freqMap = new HashMap<>();
        // 【生产实践】try-with-resources 自动关闭流，保证资源释放
        try (BufferedReader reader = Files.newBufferedReader(filePath)) {
            String line;
            // 【技术深度】逐行流式读取，内存占用与文件大小解耦
            while ((line = reader.readLine()) != null) {
                extractWords(line, freqMap);
            }
        }
        return freqMap;
    }

    // 【技术深度】手动逐字符扫描替代正则，减少开销
    private void extractWords(String line, Map<String, Integer> freqMap) {
        int n = line.length();
        StringBuilder wordBuilder = new StringBuilder();

        for (int i = 0; i < n; i++) {
            char c = line.charAt(i);
            if (Character.isLetter(c)) {
                wordBuilder.append(Character.toLowerCase(c));
            } else {
                if (wordBuilder.length() > 0) {
                    String word = wordBuilder.toString();
                    // 【技术深度】Map.merge 一行完成频次累加，简洁高效
                    freqMap.merge(word, 1, Integer::sum);
                    wordBuilder.setLength(0);
                }
            }
        }

        // 【代码质量】处理循环结束后尾部单词，防止遗漏
        if (wordBuilder.length() > 0) {
            String word = wordBuilder.toString();
            freqMap.merge(word, 1, Integer::sum);
        }
    }

    // 【问题求解】最小堆维护 TopK，O(n log k) 空间高效
    private PriorityQueue<Map.Entry<String, Integer>> buildTopKHeap(
            Map<String, Integer> frequencyMap, int topK) {
        PriorityQueue<Map.Entry<String, Integer>> minHeap = new PriorityQueue<>(
                topK, MIN_HEAP_COMPARATOR);

        for (Map.Entry<String, Integer> entry : frequencyMap.entrySet()) {
            if (minHeap.size() < topK) {
                minHeap.offer(entry);
            } else if (shouldReplace(entry, minHeap.peek())) {
                minHeap.poll();
                minHeap.offer(entry);
            }
        }
        return minHeap;
    }

    // 【代码质量】独立替换判断方法，便于单元测试
    private boolean shouldReplace(Map.Entry<String, Integer> candidate,
                                  Map.Entry<String, Integer> heapTop) {
        if (candidate.getValue() > heapTop.getValue()) {
            return true;
        }
        return candidate.getValue().equals(heapTop.getValue())
                && candidate.getKey().compareTo(heapTop.getKey()) < 0;
    }
}
