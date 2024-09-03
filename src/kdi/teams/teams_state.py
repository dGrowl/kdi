from itertools import combinations
from math import ceil, inf
from random import shuffle
from typing import Optional, Sequence

from ..util import shuffled, KeySet, MagneticGraph, NodeWeights
from .team import Team

Player = frozenset[str]


def calc_team_sizes(n_players: int, max_size: int) -> list[int]:
	if max_size <= 0 or n_players <= 0:
		return []
	n_groups = ceil(n_players / max_size)
	base_size = n_players // n_groups
	remainder = n_players % n_groups
	group_sizes = [base_size + 1] * remainder + [base_size] * (n_groups - remainder)
	return group_sizes


def build_empty_teams(pool: set[Player], max_size: int):
	n_players = sum(len(p) for p in pool)
	team_sizes = calc_team_sizes(n_players, max_size)
	shuffle(team_sizes)
	return [Team(n) for n in team_sizes]


def get_optimal_teammate(pool: set[Player], team: Team, out_forces: NodeWeights):
	optimal_player = None
	min_force = inf
	for player in pool:
		if len(player) > team.remaining_space:
			continue
		force = sum(out_forces[name] for name in player)
		if force < min_force:
			min_force = force
			optimal_player = player
	return optimal_player


class TeamsState:
	_forces: MagneticGraph
	_players: set[Player]

	def __init__(
		self,
		players: Optional[Sequence[KeySet]] = None,
	):
		self._forces = MagneticGraph()
		self._players = set()
		if players is not None:
			for p in players:
				self.add_player(p)

	def reset(self):
		self._forces.clear()
		self._players.clear()

	@property
	def players(self):
		return self._players

	def add_player(self, names: KeySet):
		for p in self._players:
			if names & p:
				return False
		new_player = Player(names)
		self._players.add(new_player)
		return True

	def remove_player(self, names: KeySet):
		player = Player(names)
		if player in self._players:
			self._players.discard(player)
			return True
		return False

	def record_historic_force(self, t: Team):
		self._forces.increment_pairs(combinations(t, 2))

	def build_priority(self):
		return shuffled(self._players)

	def fill_team(self, pool: set[Player], team: Team):
		out_forces = NodeWeights()
		for name in team:
			out_forces.update(self._forces[name])
		while pool and team.has_space:
			player = get_optimal_teammate(pool, team, out_forces)
			if player is None:
				break
			team.add_members(player)
			pool.discard(player)
			for name in player:
				out_forces.update(self._forces[name])

	def generate(self, max_team_size: int):
		pool = self._players.copy()
		priority = self.build_priority()
		teams = build_empty_teams(pool, max_team_size)
		for player in priority:
			if player not in pool:
				continue
			for t in teams:
				if t.remaining_space >= len(player):
					t.add_members(player)
					pool.discard(player)
					self.fill_team(pool, t)
					break
		for t in teams:
			self.record_historic_force(t)
		return teams
