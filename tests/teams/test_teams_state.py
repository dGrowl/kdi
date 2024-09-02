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


@pytest.fixture
def cores_2_1():
	return [{"x", "y"}, {"z"}]


@pytest.fixture
def players_3():
	return [{name} for name in "abc"]


@pytest.fixture
def players_6():
	return [{name} for name in "abcdef"]


class TestAddPlayer:
	def test_returns_true_on_success(self):
		state = TeamsState()
		assert state.add_player({"a"})

	def test_returns_false_on_duplicate(self, players_3: list[KeySet]):
		state = TeamsState(players=players_3)
		assert not state.add_player(players_3[0])


class TestRemovePlayer:
	def test_returns_true_on_success(self, players_3: list[KeySet]):
		state = TeamsState(players=players_3)
		assert state.remove_player(players_3[0])

	def test_returns_false_on_nonexistent(self):
		state = TeamsState()
		assert not state.remove_player({"a"})


class TestGenerate:
	def test_sizes_teams_correctly(self, players_6: list[KeySet]):
		state = TeamsState(players=players_6)
		teams = state.generate(3)

		for t in teams:
			assert t._capacity == 3

	def test_places_every_player(self, players_6: list[KeySet]):
		state = TeamsState(players=players_6)
		teams = state.generate(3)

		assert set().union(name for t in teams for name in t) == set().union(
			name for p in players_6 for name in p
		)

	def test_places_multiplayer_together(self):
		multi = frozenset({"e", "f"})
		players = [{c} for c in "abcd"] + [multi]
		state = TeamsState(players=players)
		teams = state.generate(3)

		assert sorted([t & multi for t in teams]) == [set(), multi]
