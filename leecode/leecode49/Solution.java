/**
 * 考点：Hash Table、String
 * 题目：Group Anagrams
 * 题目描述：给你一个字符串数组 strs，请你将字母异位词组合在一起。
 *          字母异位词（Anagram）是由重新排列源单词的所有字母得到的一个新单词。
 *          可以按任意顺序返回结果列表。
 *          所有输入字符串都为小写字母。
 * 思路：第一步：创建一个 HashMap<String, List<String>>，键为排序后的字符串，值为对应的字母异位词列表。
 *       第二步：遍历 strs 中的每个单词 str。
 *       第三步：将 str 转为字符数组 chars，排序后重新构造为字符串 key；
 *              排序后 key 相同的单词即为字母异位词。
 *       第四步：使用 map.computeIfAbsent(key, k -> new ArrayList<>()) 为 key 创建列表，并将 str 加入。
 *       第五步：遍历结束后，返回 map.values() 构造的 ArrayList，即所有分组结果。
 * 算法：哈希表 —— key 为排序后的字符串，value 为对应变位词列表。
 * 时间复杂度：O(n * k log k)，n 为字符串个数，k 为最大字符串长度
 * 空间复杂度：O(n * k)
 */
import java.util.*;

public class Solution {
    public List<List<String>> groupAnagrams(String[] strs) {
        Map<String, List<String>> map = new HashMap<>();
        for (String str : strs) {
            char[] chars = str.toCharArray();
            Arrays.sort(chars);
            String key = new String(chars);
            map.computeIfAbsent(key, k -> new ArrayList<>()).add(str);
        }
        return new ArrayList<>(map.values());
    }
}
