from typing import Sequence

from pytest_mock import MockerFixture
import pytest

from kdi.teams.teams_state import Team, TeamsState
from kdi.util import KeySet
from kdi.util.undirected_graph import STRONG_FORCE


class TestTeamMatchesBlock:
	def test_returns_true_on_match(self):
		state = TeamsState()
		state._blocks = {Team("ac")}
		assert state._team_matches_block(Team("ab"), Team("c"))

	def test_returns_false_on_no_match(self):
		state = TeamsState()
		state._blocks = {Team("ad")}
		assert not state._team_matches_block(Team("ab"), Team("c"))


class TestCalcNMaxTeams:
	@pytest.mark.parametrize(
		("n", "k", "expected"),
		[
			(10, 4, 1),
			(7, 3, 1),
			(6, 4, 2),
			(5, 4, 1),
			(5, 3, 1),
			(5, 2, 2),
			(4, 3, 2),
			(4, 4, 1),
			(2, 4, 1),
			(1, 3, 1),
		],
	)
	def test_calculates_expected_sizes(self, n: int, k: int, expected: list[int]):
		assert TeamsState._calc_n_max_teams(n, k) == expected


@pytest.fixture
def cores_2_1():
	return [{"x", "y"}, {"z"}]


@pytest.fixture
def players_3():
	return [{name} for name in "abc"]


@pytest.fixture
def players_6():
	return [{name} for name in "abcdef"]


class TestAddCore:
	def test_returns_true_on_success(self, players_3: list[KeySet]):
		state = TeamsState(players=players_3)
		assert state.add_core({"k"})

	def test_returns_false_on_failure(self, players_3: list[KeySet]):
		state = TeamsState(players=players_3)
		assert state.add_core({"x"})

	def test_adds_new_player_to_cores(self, players_3: list[KeySet]):
		state = TeamsState(players=players_3)
		state.add_core({"k"})
		assert Team("k") in state._cores

	def test_adds_existing_player_to_cores(self, players_3: list[KeySet]):
		state = TeamsState(players=players_3)
		state.add_core({"a"})
		assert Team("a") in state._cores

	def test_cleans_overlapping_players(self, players_3: list[KeySet]):
		state = TeamsState(players=players_3)
		state.add_player({"d", "e"})
		state.add_core({"d"})

		assert state._players == {Team(c) for c in "abcde"}

	def test_keep_existing_player_in_players(self, players_3: list[KeySet]):
		state = TeamsState(players=players_3)
		state.add_core({"a"})
		assert Team("a") in state._players

	def test_repels_cores_from_each_other(self, cores_2_1: list[KeySet]):
		state = TeamsState()
		state.add_core(cores_2_1[0])

		assert not state._forces["x"] and not state._forces["y"]

		state.add_core(cores_2_1[1])

		assert state._forces.calc_internal_magnetism({"x"}, {"z"}) == STRONG_FORCE
		assert state._forces.calc_internal_magnetism({"y"}, {"z"}) == STRONG_FORCE


class TestRemoveCore:
	def test_returns_true_on_success(self, cores_2_1: list[KeySet]):
		state = TeamsState(cores=cores_2_1)
		assert state.remove_core({"z"})

	def test_returns_false_on_nonexistent(self, cores_2_1: list[KeySet]):
		state = TeamsState(cores=cores_2_1)
		assert not state.remove_core({"k"})

	def test_fails_on_partial_match(self, cores_2_1: list[KeySet]):
		state = TeamsState(cores=cores_2_1)
		assert not state.remove_core({"x"})


class TestAddPlayer:
	def test_returns_true_on_success(self):
		assert TeamsState().add_player({"a"})

	def test_returns_false_on_duplicate(self, players_3: list[KeySet]):
		state = TeamsState(players=players_3)
		assert not state.add_player(players_3[0])


class TestRemovePlayer:
	def test_returns_true_on_success(self, players_3: list[KeySet]):
		state = TeamsState(players=players_3)
		assert state.remove_player(players_3[0])

	def test_returns_false_on_nonexistent(self):
		assert not TeamsState().remove_player({"a"})


class TestRecordHistoricForce:
	def test_increments_all_pairs(self):
		team = Team("abc")
		a, b, c = team
		state = TeamsState()
		state._record_historic_force(team)

		assert state._forces[a][b] == state._forces[a][c] == state._forces[b][c] == 1


@pytest.fixture
def sample_state(cores_2_1: list[KeySet], players_3: list[KeySet]):
	return TeamsState(cores_2_1, players_3)


def sort_keysets(keysets: Sequence[KeySet]):
	return sorted(keysets, key=lambda names: sorted(list(names)))


class TestFindOptimalPair:
	def test_returns_player_with_least_force(self, players_6: list[KeySet]):
		state = TeamsState(players=players_6)
		state._forces.load(
			[
				("a", "b", -1),
				("a", "c", 1),
			]
		)
		open_teams = state._players
		pair = state._find_optimal_pair(open_teams, 3)

		assert pair is not None
		assert sort_keysets(pair) == [{"a"}, {"b"}]

	def test_uses_external_force(self, cores_2_1, players_3):
		state = TeamsState(cores_2_1, players_3)
		state._forces.repel("z", "b")
		pair = state._find_optimal_pair(state._players, 3)

		assert pair is not None
		team_a, team_b = sort_keysets(pair)
		assert team_a in [{"a"}, {"c"}]
		assert team_b == {"z"}

	def test_avoids_overfilling_teams(self):
		state = TeamsState(players=[set("ab"), set("cd")])
		pair = state._find_optimal_pair(state._players, 3)

		assert pair is None

	def test_uses_historic_forces(self):
		state = TeamsState(cores=[{"a"}, {"b"}], players=[{"c"}, {"d"}])
		state._forces.increment("b", "d")
		state._forces.add("b", "c", 2)
		pair = state._find_optimal_pair(state._players, 3)

		assert pair is not None
		assert sort_keysets(pair) == [{"a"}, {"c"}]


class TestGenerate:
	def test_sizes_teams_correctly(self, players_6: list[KeySet]):
		state = TeamsState(players=players_6)
		teams = state.generate(3)

		for t in teams:
			assert len(t) == 3

	def test_places_every_player(self, players_6: list[KeySet]):
		state = TeamsState(players=players_6)
		teams = state.generate(3)

		assert set().union(name for t in teams for name in t) == set().union(
			name for p in players_6 for name in p
		)

	def test_places_multiplayer_together(self):
		multi = Team("ef")
		players = [Team(c) for c in "abcd"] + [multi]
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

	def test_splits_repulsed_players(self, cores_2_1: list[KeySet]):
		state = TeamsState(cores_2_1, [{"a"}, {"b"}])
		state._forces.repel("b", "z")
		teams = state.generate(3)

		assert "b" not in teams[0 if "z" in teams[0] else 1]

	def test_combines_attracted_players(self, cores_2_1: list[KeySet]):
		state = TeamsState(cores_2_1, [{"a"}, {"b"}])
		state._forces.attract("b", "z")
		teams = state.generate(3)

		assert "b" in teams[0 if "z" in teams[0] else 1]

	def test_records_historic_forces(
		self, mocker: MockerFixture, players_3: list[KeySet]
	):
		recorder = mocker.spy(TeamsState, "_record_historic_force")

		state = TeamsState(players=players_3)
		teams = state.generate(3)

		recorder.assert_called_once_with(state, teams[0])

	def test_follows_historic_forces(self, players_6: list[KeySet]):
		state = TeamsState(players=players_6)
		state._forces.load(
			[
				("a", "b", 4),
				("a", "c", 4),
				("a", "d", 3),
				("a", "e", -1),
				("a", "f", -1),
			]
		)
		teams = state.generate(3)

		assert teams[0 if "a" in teams[0] else 1] == set("aef")

	def test_distributes_members_no_weights(
		self,
		mocker: MockerFixture,
		cores_2_1: list[KeySet],
		players_3: list[KeySet],
	):
		mocker.patch(
			"kdi.teams.teams_state.TeamsState._find_optimal_pair",
			mocker.MagicMock(
				side_effect=[
					(Team("z"), Team("c")),
					(Team("zc"), Team("a")),
					(Team("xy"), Team("b")),
				]
			),
		)

		state = TeamsState(cores_2_1, players_3)
		teams = state.generate(3)
		assert teams == [set("acz"), set("bxy")] or teams == [set("bxy"), set("acz")]

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
