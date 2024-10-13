from itertools import combinations, product
from math import ceil, inf
from random import shuffle
from typing import Iterable, Optional, Sequence

from ..util import get_config_value, KeySet, MagneticGraph

Team = frozenset[str]


class TeamsState:
	_blocks: set[Team]
	_cores: set[Team]
	_forces: MagneticGraph
	_players: set[Team]
	_round_number: int

	def __init__(
		self,
		cores: Optional[Sequence[KeySet]] = None,
		players: Optional[Sequence[KeySet]] = None,
	):
		self._blocks = set()
		self._cores = set()
		self._forces = MagneticGraph()
		self._players = set()
		self._round_number = 0

		if cores is not None:
			for c in cores:
				self.add_core(c)
		if players is not None:
			for p in players:
				self.add_player(p)

		self._load_blocks()

	def reset(self):
		self._cores.clear()
		self._forces.clear()
		self._players.clear()
		self._round_number = 0

	def _load_blocks(self):
		for name_pair in get_config_value("teams", "blocks"):
			if len(name_pair) != 2:
				raise RuntimeError(
					"Each entry in the 'teams.blocks' config array must contain two usernames"
				)
			self._blocks.add(Team(name_pair))
			self._forces.repel(name_pair[0], name_pair[1])

	@property
	def players(self):
		return self._players

	@property
	def cores(self):
		return self._cores

	@property
	def round_number(self):
		return self._round_number

	def add_core(self, names: KeySet):
		new_core = Team(names)
		for c in self._cores:
			if new_core & c:
				return False
		self._separate_core_from_players(new_core)
		self._players.add(new_core)
		self._cores.add(new_core)
		return True

	def remove_core(self, names: KeySet):
		core = Team(names)
		if core in self._cores:
			self._cores.discard(core)
			self._players.discard(core)
			return True
		return False

	def add_player(self, names: KeySet):
		for p in self._players:
			if names & p:
				return False
		self._players.add(Team(names))
		return True

	def remove_player(self, names: KeySet):
		player = Team(names)
		self._cores.discard(player)
		if player in self._players:
			self._players.discard(player)
			return True
		return False

	def _separate_core_from_players(self, core: Team):
		players_to_add: set[Team] = set()
		players_to_remove: set[Team] = set()
		for p in self._players:
			player_without_core_members = p - core
			if len(p) != len(player_without_core_members):
				if player_without_core_members:
					players_to_add.add(player_without_core_members)
				players_to_remove.add(p)
		for c in self._cores:
			self._forces.repel_pairs(product(core, c))
		self._players -= players_to_remove
		self._players |= players_to_add

	def _record_historic_force(self, t: Team):
		self._forces.increment_pairs(combinations(t, 2))

	def _team_too_large(self, new_len: int, max_team_size: int):
		return new_len > max_team_size

	def _team_matches_block(self, t1: Team, t2: Team):
		new_team = t1 | t2
		for illegal_pair in self._blocks:
			if illegal_pair.issubset(new_team):
				return True
		return False

	@staticmethod
	def _calc_n_max_teams(n_players: int, max_team_size: int):
		n_groups = ceil(n_players / max_team_size)
		if n_groups == 0:
			return 0
		remainder = n_players % n_groups
		return remainder if remainder != 0 else n_groups

	def _find_optimal_pair(self, open_teams: set[Team], max_team_size: int):
		min_force = inf
		optimal_team_a = optimal_team_b = None
		optimal_size = 0
		pairs = list(combinations(open_teams, 2))
		shuffle(pairs)
		for t1, t2 in pairs:
			new_len = len(t1) + len(t2)
			if self._team_too_large(new_len, max_team_size) or self._team_matches_block(
				t1, t2
			):
				continue
			force = self._forces.calc_force(t1, t2, open_teams)
			if force < min_force or (force == min_force and new_len > optimal_size):
				min_force = force
				optimal_team_a = t1
				optimal_team_b = t2
				optimal_size = new_len
		if optimal_team_a is None or optimal_team_b is None:
			return None
		return optimal_team_a, optimal_team_b

	def _combine_teams(self, t1: Team, t2: Team, open_teams: set[Team]):
		open_teams.discard(t1)
		open_teams.discard(t2)
		return t1 | t2

	def generate(self, max_team_size: int):
		closed_teams = {t for t in self._players if len(t) >= max_team_size}
		open_teams = self._players - closed_teams
		n_players = sum(len(p) for p in open_teams)
		n_max_teams = self._calc_n_max_teams(n_players, max_team_size)
		while open_teams:
			pair = self._find_optimal_pair(open_teams, max_team_size)
			if pair is None:
				break
			new_team = self._combine_teams(pair[0], pair[1], open_teams)
			if len(new_team) == max_team_size:
				closed_teams.add(new_team)
				n_max_teams -= 1
				if n_max_teams == 0:
					max_team_size -= 1
			else:
				open_teams.add(new_team)
		closed_teams |= open_teams
		for t in closed_teams:
			self._record_historic_force(t)
		self._round_number += 1
		return list(closed_teams)
