import pytest

from kdi.teams.teams_state import calc_team_sizes


class TestCalcSizes:
	@pytest.mark.parametrize(
		("n", "k", "expected"),
		[
			(10, 4, [4, 3, 3]),
			(7, 3, [3, 2, 2]),
			(6, 4, [3, 3]),
			(5, 4, [3, 2]),
			(5, 3, [3, 2]),
			(5, 2, [2, 2, 1]),
			(4, 3, [2, 2]),
			(4, 4, [4]),
			(2, 4, [2]),
			(1, 3, [1]),
		],
	)
	def test_calculates_expected_sizes(self, n: int, k: int, expected: list[int]):
		assert calc_team_sizes(n, k) == expected
