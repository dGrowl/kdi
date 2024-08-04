from pytest_mock import MockerFixture
import pytest

from kdi.bot.bot import KDI
from kdi.util.config import load_config


@pytest.fixture(scope="session", autouse=True)
def use_example_config(session_mocker: MockerFixture):
	session_mocker.patch("kdi.util.config.CONFIG_FILE_NAME", "config.example.toml")
	load_config()
	session_mocker.patch("kdi.bot.bot.kdi", KDI())
