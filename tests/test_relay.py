from typing import Optional

import hikari
import lightbulb

from pytest_mock import MockType, MockerFixture
import pytest

from kdi.bot import kdi
from kdi.relay.relay import (
	CHANNEL_NOT_SET_RESPONSE,
	RelayPlugin,
	SET_CHANNEL_SUCCESS_RESPONSE,
	UNTRUSTED_USER_RESPONSE,
)


SAMPLE_USER_ID = 123

SAMPLE_CHANNEL_ID = 246


@pytest.fixture
def sample_set_channel_context(mocker: MockerFixture):
	ctx = mocker.MagicMock(spec=lightbulb.SlashContext)
	ctx.user.id = SAMPLE_USER_ID
	ctx.options = {"channel": mocker.MagicMock(spec=hikari.TextableGuildChannel)}
	ctx.options["channel"].id = SAMPLE_CHANNEL_ID
	ctx.respond = mocker.AsyncMock()
	return ctx


@pytest.fixture
def sample_dm_event(mocker: MockerFixture):
	event = mocker.MagicMock(spec=hikari.DMMessageCreateEvent)
	event.author_id = SAMPLE_USER_ID
	event.message = mocker.MagicMock()
	event.message.respond = mocker.AsyncMock()
	event.message.content = event.content = "Hi, kdi!"
	return event


@pytest.fixture
def mock_message_sender(mocker: MockerFixture):
	return mocker.patch("kdi.relay.relay.RelayPlugin.send_message", mocker.AsyncMock())


@pytest.fixture
def mock_message_creator(mocker: MockerFixture):
	return mocker.patch("hikari.impl.RESTClientImpl.create_message", mocker.AsyncMock())


class TestInit:
	def test_subscribes_to_dms(self, mocker: MockerFixture):
		subscriber = mocker.spy(hikari.GatewayBot, "subscribe")
		relay = RelayPlugin()
		subscriber.assert_called_once_with(
			kdi, hikari.DMMessageCreateEvent, relay.on_dm
		)


class TestSendMessage:
	@pytest.mark.asyncio
	async def test_sends_message(
		self, mock_message_creator: MockType, sample_dm_event: MockType
	):
		relay = RelayPlugin()
		relay._user_channel[sample_dm_event.author_id] = SAMPLE_CHANNEL_ID
		await relay.send_message(sample_dm_event)
		mock_message_creator.assert_called_once_with(
			SAMPLE_CHANNEL_ID, sample_dm_event.content
		)

	@pytest.mark.asyncio
	@pytest.mark.parametrize("content", [None, "", "/test"])
	async def test_rejects_irrelevant(
		self,
		mock_message_creator: MockType,
		sample_dm_event: MockType,
		content: Optional[str],
	):
		sample_dm_event.content = content
		relay = RelayPlugin()
		await relay.send_message(sample_dm_event)
		mock_message_creator.assert_not_called()
		sample_dm_event.message.respond.assert_not_called()

	@pytest.mark.asyncio
	async def test_rejects_unset_channel(self, sample_dm_event: MockType):
		relay = RelayPlugin()
		await relay.send_message(sample_dm_event)
		sample_dm_event.message.respond.assert_called_once_with(
			CHANNEL_NOT_SET_RESPONSE, flags=hikari.MessageFlag.EPHEMERAL
		)


class TestSetChannel:
	@pytest.mark.asyncio
	async def test_stores_user_channel(self, sample_set_channel_context: MockType):
		relay = RelayPlugin()
		await relay.set_channel(sample_set_channel_context)
		assert (
			relay._user_channel[sample_set_channel_context.user.id]
			== sample_set_channel_context.options["channel"].id
		)
		sample_set_channel_context.respond.assert_called_once_with(
			SET_CHANNEL_SUCCESS_RESPONSE, flags=hikari.MessageFlag.EPHEMERAL
		)


class TestOnDM:
	@pytest.mark.asyncio
	async def test_passes_message(
		self, sample_dm_event: MockType, mock_message_sender: MockType
	):
		relay = RelayPlugin()
		await relay.on_dm(sample_dm_event)
		mock_message_sender.assert_called_once_with(sample_dm_event)

	@pytest.mark.asyncio
	async def test_rejects_bot(
		self, sample_dm_event: MockType, mock_message_sender: MockType
	):
		sample_dm_event.is_human = False
		relay = RelayPlugin()
		await relay.on_dm(sample_dm_event)
		mock_message_sender.assert_not_called()
		sample_dm_event.message.respond.assert_not_called()

	@pytest.mark.asyncio
	async def test_rejects_untrusted(self, sample_dm_event: MockType):
		sample_dm_event.author_id = 111
		relay = RelayPlugin()
		await relay.on_dm(sample_dm_event)
		sample_dm_event.message.respond.assert_called_once_with(
			UNTRUSTED_USER_RESPONSE, flags=hikari.MessageFlag.EPHEMERAL
		)

	@pytest.mark.asyncio
	async def rejects_slash_message(
		self, mocker: MockerFixture, sample_dm_event: MockType
	):
		sample_dm_event.content = "/test"
		message_creator = mocker.patch(
			"hikari.impl.RESTClientImpl.create_message", mocker.AsyncMock()
		)
		relay = RelayPlugin()
		await relay.on_dm(sample_dm_event)
		message_creator.assert_not_called()
