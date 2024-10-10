import pytest

from kdi.util import MagneticGraph
from kdi.util.undirected_graph import STRONG_FORCE, UndirectedGraph, WEAK_FORCE


@pytest.fixture
def a():
	return "a"


@pytest.fixture
def b():
	return "b"


@pytest.fixture
def c():
	return "c"


@pytest.fixture
def d():
	return "d"


class TestAdd:
	def test_synchronizes_weights(self, a: str, b: str):
		x = 4
		graph = UndirectedGraph()
		graph.add(a, b, x)
		assert graph._weights[a][b] == graph._weights[a][b] == x

	def test_ignores_key_order(self, a: str, b: str):
		x = 4
		y = 3
		graph = UndirectedGraph()
		graph.add(a, b, x)
		graph.add(b, a, y)
		assert graph._weights[a][b] == graph._weights[a][b] == x + y


class TestResetPolarity:
	def test_resets_attraction(self, a: str, b: str):
		graph = MagneticGraph()
		graph.attract(a, b)
		graph.reset_polarity(a, b)
		assert graph[a][b] == 0

	def test_resets_repulsion(self, a: str, b: str):
		graph = MagneticGraph()
		graph.repel(a, b)
		graph.reset_polarity(a, b)
		assert graph[a][b] == 0

	def test_ignores_key_order(self, a: str, b: str):
		graph = MagneticGraph()
		graph.attract(a, b)
		graph.reset_polarity(b, a)
		assert graph[a][b] == graph[b][a] == 0

	def test_detects_existing_polarity(self, a: str, b: str, c: str):
		graph = MagneticGraph()
		graph.attract(a, b)
		graph.repel(a, c)
		graph.reset_polarity(a, c)
		assert graph[a][c] == graph[c][a] == 0


class TestAttract:
	def test_removes_repulsion(self, a: str, b: str):
		graph = MagneticGraph()
		graph.repel(a, b)
		graph.attract(a, b)
		assert b not in graph._repulsions[a]


class TestRepel:
	def test_removes_attraction(self, a: str, b: str):
		graph = MagneticGraph()
		graph.attract(a, b)
		graph.repel(a, b)
		assert b not in graph._attractions[a]


class TestCalcInternalMagnetism:
	def test_no_force_with_empty_graph(self):
		assert MagneticGraph().calc_internal_magnetism(set(), set()) == 0

	def test_adds_repulsions(self, a: str, b: str):
		graph = MagneticGraph()
		graph.repel(a, b)
		assert graph.calc_internal_magnetism({a}, {b}) == STRONG_FORCE

	def test_subtracts_attractions(self, a: str, b: str):
		graph = MagneticGraph()
		graph.attract(a, b)
		assert graph.calc_internal_magnetism({a}, {b}) == -STRONG_FORCE

	def test_returns_net(self, a: str, b: str, c: str):
		graph = MagneticGraph()
		graph.repel(a, b)
		graph.attract(c, b)
		assert graph.calc_internal_magnetism({a, c}, {b}) == 0

	def test_ignores_key_order(self, a: str, b: str):
		graph = MagneticGraph()
		graph.repel(a, b)
		assert (
			graph.calc_internal_magnetism({a}, {b})
			== graph.calc_internal_magnetism({b}, {a})
			== STRONG_FORCE
		)

	def test_ignores_interkey_forces(self, a: str, b: str, c: str):
		graph = MagneticGraph()
		graph.attract(a, c)
		assert graph.calc_internal_magnetism({a, c}, {b}) == 0

	def test_ignores_irrelevant_forces(self, a: str, b: str, c: str, d: str):
		graph = MagneticGraph()
		graph.repel(a, c)
		graph.attract(b, d)
		assert graph.calc_internal_magnetism({a}, {b}) == 0


class TestCalcExternalMagnetism:
	def test_no_force_with_empty_graph(self):
		assert MagneticGraph().calc_external_magnetism(set(), set()) == 0

	def test_adds_attractions(self, a: str, b: str, c: str):
		graph = MagneticGraph()
		graph.attract(a, c)
		assert graph.calc_external_magnetism({a, b}, {c}) == WEAK_FORCE

	def test_subtracts_repulsions(self, a: str, b: str, c: str):
		graph = MagneticGraph()
		graph.repel(a, c)
		assert graph.calc_external_magnetism({a, b}, {c}) == -WEAK_FORCE

	def test_returns_net(self, a: str, b: str, c: str, d: str):
		graph = MagneticGraph()
		graph.repel(a, c)
		graph.attract(b, d)
		assert graph.calc_external_magnetism({a, b}, {c, d}) == 0

	def test_ignores_internal_forces(self, a: str, b: str, c: str):
		graph = MagneticGraph()
		graph.attract(a, c)
		assert graph.calc_external_magnetism({a, c}, {b}) == 0

	def test_ignores_irrelevant_forces(self, a: str, b: str, c: str, d: str):
		graph = MagneticGraph()
		graph.repel(c, d)
		assert graph.calc_external_magnetism({a, b}, {c, d}) == 0


class TestCalcForce:
	def test_no_force_with_empty_graph(self):
		assert MagneticGraph().calc_force(set(), set(), set()) == 0

	def test_adds_internal_weights(self, a: str, b: str):
		graph = MagneticGraph()
		graph.load(
			[
				(a, b, 1),
			]
		)
		assert graph.calc_force({a}, {b}, set()) == 1

	def test_subtracts_external_weights(self, a: str, b: str, c: str):
		graph = MagneticGraph()
		graph.load(
			[
				(a, b, 1),
				(b, c, 2),
			]
		)
		assert graph.calc_force({a}, {b}, {a, b, c}) == -1

	def test_ignores_key_order(self, a: str, b: str):
		graph = MagneticGraph()
		graph.repel(a, b)
		assert (
			graph.calc_force({a}, {b}, {a, b})
			== graph.calc_force({b}, {a}, {a, b})
			== STRONG_FORCE
		)

	def test_combines_all_forces(self, a: str, b: str, c: str):
		graph = MagneticGraph()
		graph.load(
			[
				(a, b, 1),
				(b, c, 2),
				(a, c, 3),
			]
		)
		graph.attract(a, b)
		graph.repel(b, c)
		assert (
			graph.calc_force({a}, {b}, {a, b, c})
			== 1 - 2 - 3 - STRONG_FORCE - WEAK_FORCE
		)
