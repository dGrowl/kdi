from typing import Iterable

import pytest

from kdi.util import flatten_2d, shuffled


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
