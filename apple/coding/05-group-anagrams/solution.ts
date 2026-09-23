// Group Anagrams — 代码空壳（CoderPad 中填充）
// 将字母异位词分组（字符多重集相同的词归为一组）。

function groupAnagrams(strs: string[]): string[][] {
  // TODO: 为每个词计算规范键（排序 或 计数），相同键归一组
  return [];
}

// —— 测试（可运行验证）——
function run() {
  const sortGroups = (g: string[][]) =>
    g.map(a => a.sort()).sort((a, b) => a[0]!.localeCompare(b[0]!));

  console.log(JSON.stringify(sortGroups(groupAnagrams(["eat", "tea", "tan", "ate", "nat", "bat"]))));
  console.log(JSON.stringify(groupAnagrams([""])));   // [[""]]
  console.log(JSON.stringify(groupAnagrams(["a"])));  // [["a"]]
}

run();
