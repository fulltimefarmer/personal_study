from typing import List


class Leaderboard:
    """玩家积分榜：支持 addScore / reset / topK 三个方法。"""

    def __init__(self) -> None:
        """初始化积分榜。"""
        pass

    def addScore(self, playerId: int, score: int) -> None:
        """将玩家 playerId 加入积分榜并累加 score 分；已存在则累加。"""
        pass

    def reset(self, playerId: int) -> None:
        """从积分榜移除玩家 playerId。"""
        pass

    def topK(self, k: int) -> int:
        """返回积分榜中分数最高的前 k 个玩家的总分。"""
        pass
