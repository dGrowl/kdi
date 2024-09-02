from math import ceil
from typing import Optional

from ..util import shuffled, KeySet
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


class TeamsState:
	_players: set[Player]

	def __init__(self, players: Optional[list[KeySet]] = None):
		self._players = set()
		if players is not None:
			for p in players:
				self.add_player(p)

	def reset(self):
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

	def build_priority(self):
		return shuffled(self._players)

	def generate(self, max_team_size: int):
		n_players = sum(len(p) for p in self._players)
		team_sizes = calc_team_sizes(n_players, max_team_size)
		teams = [Team(n) for n in team_sizes]
		players = self.build_priority()
		for p in players:
			for t in teams:
				if t.remaining_space >= len(p):
					t.add_members(p)
					break
		return teams
