package com.study.coding.question4;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;

/**
 * Formats an array of words into fully-justified lines of a given width.
 *
 * <p>Approach:
 * <ol>
 *   <li>Greedily pack words into lines (each line fits as many words as possible
 *       including at least one space between them).</li>
 *   <li>For each line, compute how many extra spaces are needed and distribute them
 *       evenly between words. Left slots receive more spaces when the division is
 *       uneven.</li>
 *   <li>The final line is left-justified (no extra spacing).</li>
 * </ol>
 */
public class Solution {

    /**
     * Returns a list of fully-justified strings, each exactly {@code maxWidth} characters.
     *
     * @param words    the words to justify; must not be null and must not contain null elements
     * @param maxWidth the target width of each line; must be >= 1
     * @return an unmodifiable list of justified lines
     * @throws NullPointerException     if {@code words} is null or contains null
     * @throws IllegalArgumentException if {@code maxWidth < 1}
     */
    public List<String> fullJustify(String[] words, int maxWidth) {
        // 【代码质量】快速失败验证，确保输入有效性
        Objects.requireNonNull(words, "words must not be null");
        if (maxWidth < 1) {
            throw new IllegalArgumentException("maxWidth must be >= 1, got: " + maxWidth);
        }

        List<String> result = new ArrayList<>();
        int i = 0;
        // 【问题求解】贪心算法打包单词，明确边界条件
        while (i < words.length) {
            int lineStart = i;
            int lineLength = words[i].length();
            i++;

            while (i < words.length && lineLength + 1 + words[i].length() <= maxWidth) {
                lineLength += 1 + words[i].length();
                i++;
            }

            // 【问题求解】预计算必要参数，分离关注点
            int wordCount = i - lineStart;
            int spacesNeeded = maxWidth - totalChars(words, lineStart, i);

            // 【代码质量】边界情况处理：末行或单单词行左对齐
            if (i == words.length || wordCount == 1) {
                result.add(buildLeftJustified(words, lineStart, i, maxWidth));
            } else {
                result.add(buildFullyJustified(words, lineStart, i, spacesNeeded, wordCount));
            }
        }
        // 【生产实践】返回不可变列表，防止调用方意外修改
        return Collections.unmodifiableList(result);
    }

    private int totalChars(String[] words, int start, int end) {
        int total = 0;
        for (int j = start; j < end; j++) {
            total += words[j].length();
        }
        return total;
    }

    // 【问题求解】均匀分配空格，左倾策略处理余数
    private String buildFullyJustified(String[] words, int start, int end,
                                       int totalSpaces, int wordCount) {
        StringBuilder sb = new StringBuilder();
        int gaps = wordCount - 1;
        int spacesPerGap = totalSpaces / gaps;
        int remainder = totalSpaces % gaps;

        for (int j = start; j < end; j++) {
            sb.append(words[j]);
            if (j < end - 1) {
                // 【技术深度】三元表达式分配余数，简洁的无分支逻辑
                int spacesHere = spacesPerGap + (j - start < remainder ? 1 : 0);
                appendSpaces(sb, spacesHere);
            }
        }
        return sb.toString();
    }

    // 【代码质量】末行左对齐，保持可读性
    private String buildLeftJustified(String[] words, int start, int end, int maxWidth) {
        StringBuilder sb = new StringBuilder();
        for (int j = start; j < end; j++) {
            sb.append(words[j]);
            if (j < end - 1) {
                sb.append(' ');
            }
        }
        appendSpaces(sb, maxWidth - sb.length());
        return sb.toString();
    }

    // 【技术深度】使用 String.repeat（Java 11）优化空格拼接
    private void appendSpaces(StringBuilder sb, int count) {
        sb.append(" ".repeat(count));
    }

}
