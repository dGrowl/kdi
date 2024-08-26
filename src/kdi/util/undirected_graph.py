from collections import Counter, defaultdict
from typing import DefaultDict, Iterable

NodeWeights = Counter[str]
KeyPair = tuple[str, str]
KeyPairs = Iterable[KeyPair]


class UndirectedGraph:
	_weights: DefaultDict[str, NodeWeights]

	def __init__(self):
		self._weights = defaultdict(NodeWeights)

	def __str__(self):
		seen: set[str] = set()
		lines: list[str] = []
		for u, edges in self._weights.items():
			for v, w in edges.items():
				if v in seen:
					continue
				lines.append(f"\t{u}-{v} = {w}")
				seen |= {u, v}
		return "{\n" + "\n".join(lines) + "\n}"

	def __getitem__(self, key: str):
		return self._weights[key]

	def clear(self):
		self._weights.clear()

	def add(self, u: str, v: str, amount: int):
		self._weights[u][v] += amount
		self._weights[v][u] += amount

	def increment(self, u: str, v: str):
		self.add(u, v, 1)

	def increment_pairs(self, pairs: KeyPairs):
		for u, v in pairs:
			self.increment(u, v)
