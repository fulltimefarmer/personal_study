import heapq


class Leaderboard:
    def __init__(self):
        self.scores = {}

    def addScore(self, playerId: int, score: int) -> None:
        self.scores[playerId] = self.scores.get(playerId, 0) + score

    def reset(self, playerId: int) -> None:
        self.scores.pop(playerId, None)

    def topK(self, k: int) -> int:
        return sum(sorted(self.scores.values(), reverse=True)[:k])

    def topK_heap(self, k: int) -> int:
        return sum(heapq.nlargest(k, self.scores.values()))


if __name__ == "__main__":
    lb = Leaderboard()
    lb.addScore(1, 73)
    lb.addScore(2, 56)
    lb.addScore(3, 39)
    lb.addScore(4, 51)
    lb.addScore(5, 4)
    assert lb.topK(1) == 73
    lb.reset(1)
    lb.reset(2)
    lb.addScore(2, 51)
    assert lb.topK(3) == 141
    print("all tests passed")
