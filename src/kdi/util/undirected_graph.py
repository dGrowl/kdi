from collections import Counter, defaultdict
from itertools import product
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
		seen: set[KeyPair] = set()
		lines: list[str] = []
		for u, edges in self._weights.items():
			for v, w in edges.items():
				pair = (u, v) if u < v else (v, u)
				if pair in seen:
					continue
				lines.append(f"\t{pair[0]}-{pair[1]} = {w}")
				seen.add(pair)
		return "{\n" + "\n".join(sorted(lines)) + "\n}"

	def __getitem__(self, key: Key):
		return self._weights[key]

	def load(self, weights: list[tuple[Key, Key, int]]):
		self.clear()
		for u, v, w in weights:
			self._weights[u][v] = self._weights[v][u] = w

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
		if u in self._attractions[v]:
			self._attractions[u].discard(v)
			self._attractions[v].discard(u)
		elif u in self._repulsions[v]:
			self._repulsions[u].discard(v)
			self._repulsions[v].discard(u)

	def attract(self, u: Key, v: Key):
		self.reset_polarity(u, v)
		self._attractions[u].add(v)
		self._attractions[v].add(u)

	def attract_pairs(self, pairs: KeyPairs):
		for u, v in pairs:
			self.attract(u, v)

	def repel(self, u: Key, v: Key):
		self.reset_polarity(u, v)
		self._repulsions[u].add(v)
		self._repulsions[v].add(u)

	def repel_pairs(self, pairs: KeyPairs):
		for u, v in pairs:
			self.repel(u, v)

	def calc_internal_magnetism(self, a: KeySet, b: KeySet):
		attractions = set()
		repulsions = set()
		for u in a:
			attractions |= self._attractions[u]
			repulsions |= self._repulsions[u]
		attractions &= b
		repulsions &= b
		return STRONG_FORCE * (len(repulsions) - len(attractions))

	def calc_external_magnetism(
		self, internal_keys: KeySet, all_keysets: Iterable[KeySet]
	):
		attractions = set()
		repulsions = set()
		for name in internal_keys:
			attractions |= self._attractions[name]
			repulsions |= self._repulsions[name]
		attractions -= internal_keys
		repulsions -= internal_keys
		n_attractions = n_repulsions = 0
		for keyset in all_keysets:
			if not keyset.isdisjoint(attractions):
				attractions -= keyset
				n_attractions += 1
			if not keyset.isdisjoint(repulsions):
				repulsions -= keyset
				n_repulsions += 1
		return WEAK_FORCE * (n_attractions - n_repulsions)

	def calc_force(self, a: KeySet, b: KeySet, all_keysets: Iterable[KeySet]):
		internal_keys = a | b
		f = 0
		f += sum(self._weights[u][v] for u, v in product(a, b))
		for keys in all_keysets:
			if keys == a or keys == b:
				continue
			f -= sum(self._weights[u][v] for u, v in product(internal_keys, keys))
		f += self.calc_internal_magnetism(a, b)
		f += self.calc_external_magnetism(internal_keys, all_keysets)
		return f
