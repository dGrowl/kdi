from pytest_mock import MockType, MockerFixture
from unittest.mock import call
import hikari
import lightbulb
import pytest

from kdi.bot import kdi
from kdi.teams.teams import (
	PLAYER_AVAILABLE_ID,
	PLAYER_UNAVAILABLE_ID,
	TeamsPlugin,
	UNTRUSTED_USER_RESPONSE,
)
from kdi.teams.teams_state import TeamsState


class TestPluginInit:
	def test_subscriptions(self, mocker: MockerFixture):
		subscriber = mocker.spy(hikari.GatewayBot, "subscribe")

		teams = TeamsPlugin()

		assert subscriber.call_count == 2
		subscriber.assert_has_calls(
			[
				call(kdi, hikari.GuildMessageDeleteEvent, teams.on_gm_delete),
				call(kdi, hikari.InteractionCreateEvent, teams.on_interaction),
			]
		)


class TestPluginStart:
	@pytest.fixture
	def start_context(self, mocker: MockerFixture):
		ctx = mocker.MagicMock(spec=lightbulb.SlashContext)
		ctx.respond = mocker.AsyncMock()
		ctx.user.id = 123
		ctx.user.is_bot = False
		return ctx

	@pytest.fixture
	def state_resetter(self, mocker: MockerFixture):
		return mocker.spy(TeamsState, "reset")

	@pytest.mark.asyncio
	async def test_resets_state(
		self,
		state_resetter: MockType,
		start_context: MockType,
	):
		teams = TeamsPlugin()
		await teams.start(start_context)

		state_resetter.assert_called_once()

	@pytest.mark.asyncio
	async def test_creates_players_message(
		self,
		mocker: MockerFixture,
		start_context: MockType,
	):
		pm_creator = mocker.patch(
			"kdi.teams.players_message.PlayersMessage.create", mocker.AsyncMock()
		)

		teams = TeamsPlugin()
		await teams.start(start_context)

		pm_creator.assert_called_once_with(start_context)

	@pytest.mark.asyncio
	async def test_rejects_bot(self, state_resetter: MockType, start_context: MockType):
		start_context.user.is_bot = True

		teams = TeamsPlugin()
		await teams.start(start_context)

		state_resetter.assert_not_called()

	@pytest.mark.asyncio
	async def test_rejects_untrusted_user(
		self, state_resetter: MockType, start_context: MockType
	):
		start_context.user.id = 321

		teams = TeamsPlugin()
		await teams.start(start_context)

		start_context.respond.assert_called_once_with(
			UNTRUSTED_USER_RESPONSE, flags=hikari.MessageFlag.EPHEMERAL
		)
		state_resetter.assert_not_called()


class TestPluginOnGMDelete:
	@pytest.mark.asyncio
	async def test_checks_player_message(self, mocker: MockerFixture):
		event = mocker.MagicMock(spec=hikari.GuildMessageDeleteEvent)
		pm_delete_checker = mocker.patch(
			"kdi.teams.players_message.PlayersMessage.check_delete", mocker.AsyncMock()
		)

		teams = TeamsPlugin()
		await teams.on_gm_delete(event)

		pm_delete_checker.assert_called_once()


SAMPLE_PLAYER_NAME = "Player A"


@pytest.fixture
def player_interaction(mocker: MockerFixture):
	interaction = mocker.MagicMock(spec=hikari.ComponentInteraction)
	interaction.create_initial_response = mocker.AsyncMock()
	interaction.custom_id = PLAYER_AVAILABLE_ID
	interaction.message = mocker.MagicMock(spec=hikari.Message)
	interaction.message.id = 248
	interaction.user.is_bot = False
	interaction.user.username = SAMPLE_PLAYER_NAME
	return interaction


@pytest.fixture
def player_interaction_event(mocker: MockerFixture, player_interaction: MockType):
	event = mocker.MagicMock(spec=hikari.InteractionCreateEvent)
	event.interaction = player_interaction
	return event


class TestCheckPlayersInteraction:
	@pytest.fixture
	def state_player_adder(self, mocker: MockerFixture):
		return mocker.spy(TeamsState, "add_player")

	@pytest.fixture
	def state_player_remover(self, mocker: MockerFixture):
		return mocker.spy(TeamsState, "remove_player")

	@pytest.mark.asyncio
	async def test_player_available(
		self, player_interaction: MockType, state_player_adder: MockType
	):
		player = {player_interaction.user.username}

		teams = TeamsPlugin()
		teams._players_message._message = player_interaction.message
		await teams.check_players_interaction(player_interaction)

		state_player_adder.assert_called_once_with(
			teams._state,
			player,
		)
		assert state_player_adder.spy_return
		player_interaction.create_initial_response.assert_called_once_with(
			hikari.ResponseType.MESSAGE_UPDATE,
			embed=teams._players_message.build_embed([player]),
		)

	@pytest.mark.asyncio
	async def test_player_unavailable(
		self, player_interaction: MockType, state_player_remover: MockType
	):
		player_interaction.custom_id = PLAYER_UNAVAILABLE_ID
		player = {player_interaction.user.username}

		teams = TeamsPlugin()
		teams._players_message._message = player_interaction.message
		teams._state.add_player(player)
		await teams.check_players_interaction(player_interaction)

		state_player_remover.assert_called_once_with(teams._state, player)
		assert state_player_remover.spy_return
		player_interaction.create_initial_response.assert_called_once_with(
			hikari.ResponseType.MESSAGE_UPDATE,
			embed=teams._players_message.build_embed([]),
		)

	@pytest.mark.asyncio
	async def test_player_available_duplicate(
		self, player_interaction: MockType, state_player_adder: MockType
	):
		player = {player_interaction.user.username}

		teams = TeamsPlugin()
		teams._players_message._message = player_interaction.message
		teams._state.add_player(player)
		await teams.check_players_interaction(player_interaction)

		state_player_adder.assert_called_with(
			teams._state,
			player,
		)
		assert not state_player_adder.spy_return

	@pytest.mark.asyncio
	async def test_player_unavailable_nonexistent(
		self, player_interaction: MockType, state_player_remover: MockType
	):
		player = {player_interaction.user.username}
		player_interaction.custom_id = PLAYER_UNAVAILABLE_ID

		teams = TeamsPlugin()
		teams._players_message._message = player_interaction.message
		await teams.check_players_interaction(player_interaction)

		state_player_remover.assert_called_once_with(teams._state, player)
		assert not state_player_remover.spy_return


class TestPluginOnInteraction:
	@pytest.mark.asyncio
	async def test_player_available(
		self, mocker: MockerFixture, player_interaction_event: MockType
	):
		mock_check_player_interaction = mocker.patch(
			"kdi.teams.teams.TeamsPlugin.check_players_interaction", mocker.AsyncMock()
		)

		teams = TeamsPlugin()
		await teams.on_interaction(player_interaction_event)

		mock_check_player_interaction.assert_called_once_with(
			player_interaction_event.interaction
		)
