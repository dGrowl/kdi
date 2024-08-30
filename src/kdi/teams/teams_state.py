from typing import Optional

from ..util import KeySet

Player = frozenset[str]


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
