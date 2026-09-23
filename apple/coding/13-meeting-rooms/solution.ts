// Meeting Rooms — 代码空壳（CoderPad 中填充）
// 判断是否能参加全部会议（无时间重叠）。

function canAttendMeetings(intervals: number[][]): boolean {
  // TODO: 按开始时间排序，检查相邻区间是否重叠
  return true;
}

// —— 测试（可运行验证）——
function run() {
  console.log(canAttendMeetings([[0, 30], [5, 10], [15, 20]])); // false
  console.log(canAttendMeetings([[7, 10], [2, 4]]));            // true
  console.log(canAttendMeetings([]));                           // true
  console.log(canAttendMeetings([[1, 4], [4, 5]]));             // true（结束==开始不重叠）
}

run();
