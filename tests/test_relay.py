import hikari

from pytest_mock import MockType, MockerFixture
import pytest

from kdi.bot import kdi
from kdi.relay import RelayPlugin
from kdi.relay.relay import (
	CHANNEL_NOT_SET_RESPONSE,
	INVALID_CHANNEL_ID_RESPONSE,
	SET_CHANNEL_SUCCESS_RESPONSE,
	UNRECOGNIZED_COMMAND_RESPONSE,
	UNTRUSTED_USER_RESPONSE,
)


@pytest.fixture
def sample_dm_event(mocker: MockerFixture):
	event = mocker.MagicMock(spec=hikari.DMMessageCreateEvent)
	event.author_id = 123
	event.message = mocker.MagicMock()
	event.message.respond = mocker.AsyncMock()
	event.message.content = event.content = "Hi, kdi!"
	return event


class TestInit:
	def test_subscribes_to_dms(self, mocker: MockerFixture):
		subscriber = mocker.spy(hikari.GatewayBot, "subscribe")
		relay = RelayPlugin()
		subscriber.assert_called_once_with(
			kdi, hikari.DMMessageCreateEvent, relay.handle_dm
		)


class TestSetChannel:
	@pytest.mark.asyncio
	async def test_success(self, sample_dm_event: MockType):
		channel_id = 135
		relay = RelayPlugin()
		await relay.set_channel(sample_dm_event, [str(channel_id)])
		assert relay.user_channel[sample_dm_event.author_id] == channel_id
		sample_dm_event.message.respond.assert_called_once_with(
			SET_CHANNEL_SUCCESS_RESPONSE
		)

	@pytest.mark.asyncio
	async def test_invalid_id(self, sample_dm_event: MockType):
		relay = RelayPlugin()
		await relay.set_channel(sample_dm_event, ["135A"])
		assert sample_dm_event.author_id not in relay.user_channel
		sample_dm_event.message.respond.assert_called_once_with(
			INVALID_CHANNEL_ID_RESPONSE
		)


class TestHandleDM:
	@pytest.mark.asyncio
	async def test_sets_channel(self, mocker: MockerFixture, sample_dm_event: MockType):
		channel_id = "246"
		sample_dm_event.content = f"/relay channel {channel_id}"
		channel_setter = mocker.patch(
			"kdi.relay.RelayPlugin.set_channel", mocker.AsyncMock()
		)
		relay = RelayPlugin()
		await relay.handle_dm(sample_dm_event)
		channel_setter.assert_called_once_with(sample_dm_event, [channel_id])

	@pytest.mark.asyncio
	async def test_sends_message(
		self, mocker: MockerFixture, sample_dm_event: MockType
	):
		channel_id = 246
		message_creator = mocker.patch(
			"hikari.impl.RESTClientImpl.create_message", mocker.AsyncMock()
		)
		relay = RelayPlugin()
		relay.user_channel[sample_dm_event.author_id] = channel_id
		await relay.handle_dm(sample_dm_event)
		message_creator.assert_called_once_with(channel_id, sample_dm_event.content)

	@pytest.mark.asyncio
	async def test_sends_help(self, sample_dm_event: MockType):
		sample_dm_event.content = "/relay unrecognized"
		relay = RelayPlugin()
		await relay.handle_dm(sample_dm_event)
		sample_dm_event.message.respond.assert_called_once_with(
			UNRECOGNIZED_COMMAND_RESPONSE
		)

	@pytest.mark.asyncio
	async def test_rejects_bot(self, sample_dm_event: MockType):
		sample_dm_event.is_human = False
		relay = RelayPlugin()
		await relay.handle_dm(sample_dm_event)
		sample_dm_event.message.respond.assert_not_called()

	@pytest.mark.asyncio
	@pytest.mark.parametrize("content", [None, ""])
	async def test_rejects_empty(self, sample_dm_event: MockType, content: str | None):
		sample_dm_event.content = content
		relay = RelayPlugin()
		await relay.handle_dm(sample_dm_event)
		sample_dm_event.message.respond.assert_not_called()

	@pytest.mark.asyncio
	async def test_rejects_untrusted(self, sample_dm_event: MockType):
		sample_dm_event.author_id = 987
		relay = RelayPlugin()
		await relay.handle_dm(sample_dm_event)
		sample_dm_event.message.respond.assert_called_once_with(UNTRUSTED_USER_RESPONSE)

	@pytest.mark.asyncio
	async def test_rejects_unset_channel(self, sample_dm_event: MockType):
		relay = RelayPlugin()
		await relay.handle_dm(sample_dm_event)
		sample_dm_event.message.respond.assert_called_once_with(
			CHANNEL_NOT_SET_RESPONSE
		)
