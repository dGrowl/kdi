from itertools import zip_longest
from typing import Sequence

from pytest_mock import MockerFixture
import pytest

from kdi.teams.team import Team
from kdi.teams.teams_state import calc_team_sizes, Player, TeamsState
from kdi.util import KeySet, NodeWeights
from kdi.util.undirected_graph import STRONG_FORCE


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

	def test_repels_cores_from_each_other(self, cores_2_1: list[KeySet]):
		state = TeamsState()
		state.add_player(cores_2_1[0], True)

		assert not state._forces["x"] and not state._forces["y"]

		state.add_player(cores_2_1[1], True)

		assert state._forces["x"]["z"] == state._forces["y"]["z"] == STRONG_FORCE


class TestRemovePlayer:
	def test_returns_true_on_success(self, players_3: list[KeySet]):
		state = TeamsState(players=players_3)
		assert state.remove_player(players_3[0])

	def test_returns_false_on_nonexistent(self):
		state = TeamsState()
		assert not state.remove_player({"a"})


class TestRecordHistoricForce:
	def test_increments_all_pairs(self):
		team = Team(3, set("abc"))
		a, b, c = team
		state = TeamsState()
		state.record_historic_force(team)

		assert state._forces[a][b] == state._forces[a][c] == state._forces[b][c] == 1


@pytest.fixture
def sample_state(cores_2_1: list[KeySet], players_3: list[KeySet]):
	return TeamsState(cores_2_1, players_3)


def sort_keysets(keysets: Sequence[KeySet]):
	return sorted(keysets, key=lambda names: sorted(list(names)))


class TestBuildPriority:
	def test_orders_all_players(
		self, sample_state: TeamsState, cores_2_1: list[KeySet], players_3: list[KeySet]
	):
		order = sample_state.build_priority()
		assert sort_keysets(order) == sort_keysets(cores_2_1 + players_3)

	def test_prioritizes_size(self, sample_state: TeamsState, cores_2_1: list[KeySet]):
		order = sample_state.build_priority()
		assert order[0] == cores_2_1[0]

	def test_prioritizes_strong_force_count(
		self, sample_state: TeamsState, cores_2_1: list[KeySet]
	):
		order = sample_state.build_priority()
		assert order[1] == cores_2_1[1]


class TestGetOptimalTeammate:
	def test_returns_player_with_least_force(self, players_6: list[KeySet]):
		state = TeamsState(players=players_6)
		pool = state._players.copy() - {Player(name) for name in "ab"}
		t = Team(3, set("ab"))
		out_forces = NodeWeights({"f": -1})

		assert state.get_optimal_teammate(pool, t, out_forces) == {"f"}

	def test_uses_max_force(self):
		pool = {Player(name) for name in ["bc", "d"]}
		t = Team(3, set("a"))
		out_forces = NodeWeights({"b": -20, "c": 10, "d": -1})

		assert TeamsState().get_optimal_teammate(pool, t, out_forces) == {"d"}

	def test_ignores_oversized_players(self):
		pool = {Player(name) for name in ["cd", "e"]}
		t = Team(3, set("ab"))
		out_forces = NodeWeights({"c": -1, "e": 1})

		assert TeamsState().get_optimal_teammate(pool, t, out_forces) == {"e"}


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
		multi = Player("ef")
		players = [Player(c) for c in "abcd"] + [multi]
		state = TeamsState(players=players)
		teams = state.generate(3)

		assert sorted([t & multi for t in teams]) == [set(), multi]

	def test_splits_cores(self, players_3: list[KeySet]):
		state = TeamsState([{"x"}, {"y"}], players_3)
		teams = state.generate(3)
		first_core = teams[0] & {"x", "y"}
		second_core = teams[1] & {"x", "y"}

		assert (first_core == {"x"} and second_core == {"y"}) or (
			first_core == {"y"} and second_core == {"x"}
		)

	def test_splits_repulsed_players(
		self, mocker: MockerFixture, cores_2_1: list[KeySet]
	):
		mocker.patch(
			"kdi.teams.teams_state.build_empty_teams",
			mocker.MagicMock(return_value=[Team(3), Team(2)]),
		)

		state = TeamsState(cores_2_1, [{"a"}, {"b"}])
		state._forces.repel("b", "z")
		teams = state.generate(3)

		assert "b" not in teams[0 if "z" in teams[0] else 1]

	def test_combines_attracted_players(
		self, mocker: MockerFixture, cores_2_1: list[KeySet]
	):
		mocker.patch(
			"kdi.teams.teams_state.build_empty_teams",
			mocker.MagicMock(return_value=[Team(3), Team(2)]),
		)

		state = TeamsState(cores_2_1, [{"a"}, {"b"}])
		state._forces.attract("b", "z")
		teams = state.generate(3)

		assert "b" in teams[0 if "z" in teams[0] else 1]

	def test_records_historic_forces(
		self, mocker: MockerFixture, players_3: list[KeySet]
	):
		recorder = mocker.spy(TeamsState, "record_historic_force")

		state = TeamsState(players=players_3)
		teams = state.generate(3)

		recorder.assert_called_once_with(state, teams[0])

	def test_follows_historic_forces(
		self, mocker: MockerFixture, players_6: list[KeySet]
	):
		mocker.patch(
			"kdi.teams.teams_state.TeamsState.build_priority",
			mocker.MagicMock(return_value=players_6),
		)

		state = TeamsState(players=players_6)
		state._forces.load(
			[
				("a", "b", 3),
				("a", "c", 3),
				("a", "d", 2),
			]
		)
		teams = state.generate(3)

		assert teams[0].members == set("aef")

	@pytest.mark.parametrize(
		("cores", "players", "max_team_size", "expected_teams"),
		[
			([], [], 3, []),
			([], [{"a"}, {"b"}, {"c"}, {"d"}], 4, [{"a", "b", "c", "d"}]),
			([], [{"a"}, {"b"}, {"c"}, {"d"}], 2, [{"a", "b"}, {"c", "d"}]),
			([{"x"}, {"y"}], [{"a"}, {"b"}, {"c"}], 3, [{"x", "a", "b"}, {"y", "c"}]),
			(
				[{"x", "y"}, {"z"}],
				[{"a"}, {"b"}, {"c"}],
				4,
				[{"x", "y", "a"}, {"z", "b", "c"}],
			),
		],
	)
	def test_distributes_members_no_weights(
		self,
		mocker: MockerFixture,
		cores: list[KeySet],
		players: list[KeySet],
		max_team_size: int,
		expected_teams: list[set[str]],
	):
		mocker.patch(
			"kdi.teams.teams_state.TeamsState.build_priority",
			mocker.MagicMock(return_value=cores + players),
		)
		mocker.patch(
			"kdi.teams.teams_state.TeamsState.get_optimal_teammate",
			mocker.MagicMock(side_effect=players),
		)
		mocker.patch(
			"kdi.teams.teams_state.build_empty_teams",
			mocker.MagicMock(return_value=[Team(len(t)) for t in expected_teams]),
		)

		state = TeamsState(cores, players)
		teams = state.generate(max_team_size)
		for team, members in zip_longest(teams, expected_teams):
			assert team._members == members

	def test_picks_larger_players_first(self, sample_state: TeamsState):
		teams = sample_state.generate(3)
		assert teams[0] & {"x", "y", "z"} == {"x", "y"}

	def test_follows_repulsion(self, sample_state: TeamsState):
		sample_state._forces.repel("a", "z")
		teams = sample_state.generate(3)
		for t in teams:
			if "a" in t:
				assert "z" not in t
				break

	def test_follows_attraction(self, sample_state: TeamsState):
		sample_state._forces.attract("a", "z")
		teams = sample_state.generate(3)
		for t in teams:
			if "a" in t:
				assert "z" in t
				break
