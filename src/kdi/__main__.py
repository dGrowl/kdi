import hikari

from .bot import kdi


if __name__ == "__main__":

	@kdi.listen(hikari.GuildMessageCreateEvent)
	async def ping(event: hikari.GuildMessageCreateEvent):
		if not event.is_human:
			return

		me = kdi.get_me()

		if (
			not me
			or not event.message.user_mentions_ids
			or me.id not in event.message.user_mentions_ids
		):
			return

		await event.message.respond("Hello, user!")

	kdi.run()
