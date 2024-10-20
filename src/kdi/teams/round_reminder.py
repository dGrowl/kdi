from typing import Optional

from lightbulb.ext import tasks
import hikari
import lightbulb

from ..bot import kdi
from ..util import get_config_value

TWENTY_MINUTES_SECS = 60 * 20

ROUND_REMINDER_CRON = get_config_value("teams", "round_reminder_cron")


class RoundReminder:
	_channel_id: Optional[hikari.Snowflakeish]
	_prev_message: Optional[hikari.Message]
	_role: Optional[hikari.Role]

	def __init__(self):
		self._channel_id = None
		self._prev_message = None
		self._role = None

	def start(self, ctx: lightbulb.SlashContext):
		self._channel_id = ctx.channel_id
		self._role = ctx.options["reminder-role"]
		self.task.start()

	def stop(self):
		self.task.cancel()

	async def send(self):
		if self._channel_id is None or self._role is None:
			return
		self._prev_message = await kdi.rest.create_message(
			self._channel_id,
			f"{self._role.mention} Please prepare for the next round!",
			role_mentions=True,
		)

	@tasks.task(tasks.CronTrigger(ROUND_REMINDER_CRON), max_executions=8)
	async def task(self):
		if self._prev_message is not None:
			await self._prev_message.delete()
			self._prev_message = None
		await self.send()
