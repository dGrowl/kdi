from collections import Counter, defaultdict
from typing import DefaultDict, Iterable, Union

Key = str
KeyPair = tuple[Key, Key]
KeyPairs = Iterable[KeyPair]
KeySet = Union[set[Key], frozenset[Key]]
NodeWeights = Counter[Key]


class UndirectedGraph:
	_weights: DefaultDict[Key, NodeWeights]

	def __init__(self):
		self._weights = defaultdict(NodeWeights)

	def __str__(self):
		seen: set[Key] = set()
		lines: list[str] = []
		for u, edges in self._weights.items():
			for v, w in edges.items():
				if v in seen:
					continue
				lines.append(f"\t{u}-{v} = {w}")
				seen |= {u, v}
		return "{\n" + "\n".join(lines) + "\n}"

	def __getitem__(self, key: Key):
		return self._weights[key]

	def clear(self):
		self._weights.clear()

	def add(self, u: Key, v: Key, amount: int):
		self._weights[u][v] += amount
		self._weights[v][u] += amount

	def increment(self, u: Key, v: Key):
		self.add(u, v, 1)

	def increment_pairs(self, pairs: KeyPairs):
		for u, v in pairs:
			self.increment(u, v)


WEAK_FORCE = 1_000
STRONG_FORCE = WEAK_FORCE * 1_000


class MagneticGraph(UndirectedGraph):
	_attractions: DefaultDict[Key, set[Key]]
	_repulsions: DefaultDict[Key, set[Key]]

	def __init__(self):
		super().__init__()
		self._attractions = defaultdict(set)
		self._repulsions = defaultdict(set)

	def __getitem__(self, u: Key):
		return self._weights[u]

	def clear(self):
		super().clear()
		self._attractions.clear()
		self._repulsions.clear()

	def reset_polarity(self, u: Key, v: Key):
		if u in self._attractions:
			self.add(u, v, STRONG_FORCE)
			self._attractions[u].discard(v)
			self._attractions[v].discard(u)
		elif u in self._repulsions:
			self.add(u, v, -STRONG_FORCE)
			self._repulsions[u].discard(v)
			self._repulsions[v].discard(u)

	def attract(self, u: Key, v: Key):
		self.reset_polarity(u, v)
		self.add(u, v, -STRONG_FORCE)
		self._attractions[u].add(v)
		self._attractions[v].add(u)

	def attract_pairs(self, pairs: KeyPairs):
		for u, v in pairs:
			self.attract(u, v)

	def repel(self, u: Key, v: Key):
		self.reset_polarity(u, v)
		self.add(u, v, STRONG_FORCE)
		self._repulsions[u].add(v)
		self._repulsions[v].add(u)

	def repel_pairs(self, pairs: KeyPairs):
		for u, v in pairs:
			self.repel(u, v)
