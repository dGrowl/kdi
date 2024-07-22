class TestBot:
	def test_loads_token(self):
		from kdi.bot.bot import kdi

		assert kdi._token == "DISCORD_API_TOKEN"  # type: ignore
