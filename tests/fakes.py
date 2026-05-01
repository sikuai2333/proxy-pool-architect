from __future__ import annotations

from collections.abc import Mapping


class FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.sorted_sets: dict[str, dict[str, float]] = {}
        self.sets: dict[str, set[str]] = {}

    async def set(self, name: str, value: str) -> bool:
        self.values[name] = value
        return True

    async def setex(self, name: str, time: int, value: str) -> bool:
        self.values[name] = value
        return True

    async def get(self, name: str) -> str | None:
        return self.values.get(name)

    async def delete(self, *names: str) -> int:
        removed = 0
        for name in names:
            if name in self.values:
                removed += 1
                del self.values[name]
            if name in self.sorted_sets:
                removed += 1
                del self.sorted_sets[name]
            if name in self.sets:
                removed += 1
                del self.sets[name]
        return removed

    async def zadd(self, name: str, mapping: Mapping[str, float]) -> int:
        sorted_set = self.sorted_sets.setdefault(name, {})
        added = 0
        for member, score in mapping.items():
            if member not in sorted_set:
                added += 1
            sorted_set[member] = score
        return added

    async def zrem(self, name: str, *values: str) -> int:
        sorted_set = self.sorted_sets.setdefault(name, {})
        removed = 0
        for value in values:
            if value in sorted_set:
                removed += 1
                del sorted_set[value]
        return removed

    async def zcard(self, name: str) -> int:
        return len(self.sorted_sets.get(name, {}))

    async def zcount(self, name: str, min: float | str, max: float | str) -> int:
        sorted_set = self.sorted_sets.get(name, {})
        min_score = float("-inf") if min == "-inf" else float(min)
        max_score = float("inf") if max == "+inf" else float(max)
        return sum(1 for score in sorted_set.values() if min_score <= score <= max_score)

    async def zrevrange(self, name: str, start: int, end: int) -> list[str]:
        sorted_set = self.sorted_sets.get(name, {})
        members = sorted(sorted_set, key=lambda member: (-sorted_set[member], member))
        stop = None if end == -1 else end + 1
        return members[start:stop]

    async def zrevrangebyscore(
        self,
        name: str,
        max: float | str,
        min: float | str,
        start: int | None = None,
        num: int | None = None,
    ) -> list[str]:
        sorted_set = self.sorted_sets.get(name, {})
        min_score = float("-inf") if min == "-inf" else float(min)
        max_score = float("inf") if max == "+inf" else float(max)
        members = [
            member for member, score in sorted_set.items() if min_score <= score <= max_score
        ]
        members.sort(key=lambda member: (-sorted_set[member], member))
        if start is None:
            return members
        stop = None if num is None else start + num
        return members[start:stop]

    async def zincrby(self, name: str, amount: float, value: str) -> float:
        sorted_set = self.sorted_sets.setdefault(name, {})
        sorted_set[value] = sorted_set.get(value, 0.0) + amount
        return sorted_set[value]

    async def sadd(self, name: str, *values: str) -> int:
        target = self.sets.setdefault(name, set())
        before = len(target)
        target.update(values)
        return len(target) - before

    async def smembers(self, name: str) -> set[str]:
        return set(self.sets.get(name, set()))
