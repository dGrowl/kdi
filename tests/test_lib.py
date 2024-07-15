import pytest

from kdi import fibonacci


class TestFibonacci:
	@pytest.mark.parametrize("x,y", [(0, 0), (1, 1)])
	def test_base_cases(self, x: int, y: int):
		assert fibonacci(x) == y

	@pytest.mark.parametrize("x,y", [(2, 1), (27, 196418), (42, 267914296)])
	def test_iteration(self, x: int, y: int):
		assert fibonacci(x) == y
