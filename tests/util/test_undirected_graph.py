import pytest

from kdi.util.undirected_graph import UndirectedGraph


@pytest.fixture
def a():
	return "a"


@pytest.fixture
def b():
	return "b"


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
