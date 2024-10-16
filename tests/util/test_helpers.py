from typing import Iterable

import pytest

from kdi.util import clamp, flatten_2d, shuffled


class TestClamp:
	@pytest.mark.parametrize(
		("x", "lo", "hi", "y"),
		[
			(3, 1, 5, 3),
			(1, 1, 5, 1),
			(5, 1, 5, 5),
			(0, 1, 5, 1),
			(-7, 1, 5, 1),
			(8, 1, 5, 5),
			(-7, -5, 5, -5),
			(3, -5, 5, 3),
			(13, -5, 5, 5),
			(-7, -5, -1, -5),
			(3, -5, -1, -1),
			(-3, -5, -1, -3),
		],
	)
	def test_returns_expected_value(self, x: int, lo: int, hi: int, y: int):
		assert clamp(x, lo, hi) == y


class TestShuffled:
	def test_copies_object(self):
		x = [1, 2, 3, 4]
		y = shuffled(x)
		assert id(x) != id(y)

	def test_copies_subobjects(self):
		x = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
		y = shuffled(x)
		for a, b in zip(x, y):
			assert id(a) != id(b)


class TestFlatten2d:
	@pytest.mark.parametrize(
		("x", "y"),
		[
			([[1], [2, 3]], [1, 2, 3]),
			([(1, 2), (3, 4)], [1, 2, 3, 4]),
		],
	)
	def test_ordered(self, x: Iterable[Iterable[int]], y: Iterable[int]):
		assert flatten_2d(x) == y

	@pytest.mark.parametrize(
		("x", "y"),
		[
			([{1}, {2, 3}], [1, 2, 3]),
			({(1, 2), (3, 4, 5)}, [1, 2, 3, 4, 5]),
			([(1, 2), {3, 4}, [5]], [1, 2, 3, 4, 5]),
		],
	)
	def test_unordered(self, x: Iterable[Iterable[int]], y: Iterable[int]):
		assert sorted(flatten_2d(x)) == y
