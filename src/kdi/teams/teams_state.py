from itertools import combinations, product
from math import ceil, inf
from random import random, shuffle
from typing import Optional, Sequence

from ..util import KeySet, MagneticGraph, NodeWeights
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


class TeamsState:
	_cores: set[Player]
	_forces: MagneticGraph
	_players: set[Player]

	def __init__(
		self,
		cores: Optional[Sequence[KeySet]] = None,
		players: Optional[Sequence[KeySet]] = None,
	):
		self._cores = set()
		self._forces = MagneticGraph()
		self._players = set()
		if cores is not None:
			for c in cores:
				self.add_core(c)
		if players is not None:
			for p in players:
				self.add_player(p)

	def reset(self):
		self._cores.clear()
		self._forces.clear()
		self._players.clear()

	@property
	def players(self):
		return self._players

	@property
	def cores(self):
		return self._cores

	def add_core(self, names: KeySet):
		new_core = Player(names)
		for c in self._cores:
			if new_core & c:
				return False
		players_to_add: set[Player] = set()
		players_to_remove: set[Player] = set()
		for p in self._players:
			player_without_core_members = p - new_core
			if len(p) != len(player_without_core_members):
				if player_without_core_members:
					players_to_add.add(player_without_core_members)
				players_to_remove.add(p)
		for c in self._cores:
			self._forces.repel_pairs(product(new_core, c))
		self._players -= players_to_remove
		self._players |= players_to_add
		self._players.add(new_core)
		self._cores.add(new_core)
		return True

	def remove_core(self, names: KeySet):
		core = Player(names)
		if core in self._cores:
			self._cores.discard(core)
			self._players.discard(core)
			return True
		return False

	def add_player(self, names: KeySet):
		for p in self._players:
			if names & p:
				return False
		self._players.add(Player(names))
		return True

	def remove_player(self, names: KeySet):
		player = Player(names)
		self._cores.discard(player)
		if player in self._players:
			self._players.discard(player)
			return True
		return False

	def record_historic_force(self, t: Team):
		self._forces.increment_pairs(combinations(t, 2))

	def build_priority(self):
		return sorted(
			self._players,
			key=lambda p: (len(p), self._forces.calc_magnetic_force_count(p), random()),
			reverse=True,
		)

	def calc_player_force(
		self, player: Player, out_forces: NodeWeights, external_names: KeySet
	):
		historic = external = -inf
		for name in player:
			historic = max(historic, out_forces[name])
			external = max(
				external,
				self._forces.calc_external_force(name, external_names),
			)
		return historic + external

	def get_optimal_teammate(
		self, pool: set[Player], team: Team, out_forces: NodeWeights
	):
		optimal_player = None
		min_force = inf
		external_names = {name for p in pool for name in p}
		for player in pool:
			if len(player) > team.remaining_space:
				continue
			force = self.calc_player_force(player, out_forces, external_names)
			if force < min_force:
				min_force = force
				optimal_player = player
		return optimal_player

	def fill_team(self, pool: set[Player], team: Team):
		out_forces = NodeWeights()
		for name in team:
			out_forces.update(self._forces[name])
		while pool and team.has_space:
			player = self.get_optimal_teammate(pool, team, out_forces)
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
