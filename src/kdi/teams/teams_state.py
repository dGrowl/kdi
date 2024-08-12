class TeamsState:
	_players: set[str]

	def __init__(self):
		self._players = set()

	def reset(self):
		self._players.clear()

	@property
	def players(self):
		return self._players

	def add_player(self, name: str):
		if name not in self._players:
			self._players.add(name)
			return True
		return False

	def remove_player(self, name: str):
		if name in self._players:
			self._players.discard(name)
			return True
		return False
