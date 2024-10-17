from typing import Optional

from lightbulb.ext import tasks
import hikari
import lightbulb

from ..util import get_config_value

TWENTY_MINUTES_SECS = 60 * 20

ROUND_REMINDER_CRON = get_config_value("teams", "round_reminder_cron")


class RoundReminder:
	_ctx: Optional[lightbulb.SlashContext]
	_role: Optional[hikari.Role]

	def __init__(self):
		self._ctx = None
		self._role = None

	def start(self, ctx: lightbulb.SlashContext):
		self._ctx = ctx
		self._role = ctx.options["reminder-role"]
		self.task.start()

	def stop(self):
		self.task.cancel()

	async def send(self):
		if not self._ctx or not self._role:
			return
		await self._ctx.respond(
			f"{self._role.mention} Please prepare for the next round!",
			delete_after=TWENTY_MINUTES_SECS,
		)

	@tasks.task(tasks.CronTrigger(ROUND_REMINDER_CRON), max_executions=12)
	async def task(self):
		await self.send()
