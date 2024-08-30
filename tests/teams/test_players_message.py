from kdi.teams.players_message import format_players


class TestFormatPlayers:
	def test_returns_empty_on_empty(self):
		assert format_players([]) == []

	def test_sorts_names(self):
		players = [{"b"}, {"c"}, {"a"}]
		assert format_players(players) == sorted(name for p in players for name in p)

	def test_formats_multiples(self):
		players = [{"b"}, {"d", "c"}, {"a"}]
		assert format_players(players) == ["a", "b", "c / d"]
