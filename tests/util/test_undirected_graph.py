import pytest

from kdi.util import MagneticGraph
from kdi.util.undirected_graph import UndirectedGraph, STRONG_FORCE


@pytest.fixture
def a():
	return "a"


@pytest.fixture
def b():
	return "b"


@pytest.fixture
def c():
	return "c"


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
		assert graph[a][b] == -STRONG_FORCE


class TestRepel:
	def test_removes_attraction(self, a: str, b: str):
		graph = MagneticGraph()
		graph.attract(a, b)
		graph.repel(a, b)
		assert graph[a][b] == STRONG_FORCE
