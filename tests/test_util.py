from typing import Any

from pytest_mock import MockerFixture
import pytest

from kdi.util import Config


@pytest.fixture(autouse=True)
def clear_config_file_data(mocker: MockerFixture):
	mocker.patch("kdi.util.config.config_file_data", None)


@pytest.fixture
def mock_config_file(mocker: MockerFixture):
	mocker.patch(
		"kdi.util.config.read_config_file",
		return_value={"section": {"a": "first", "b": "second"}},
	)


@pytest.fixture
def sample_config():
	return Config("section", {"a", "b"})


class TestConfig:
	def test_loads_keys(
		self,
		sample_config: Config,
		mock_config_file: None,
	):
		assert sample_config.get("a") == "first"
		assert sample_config.get("b") == "second"

	def test_reads_file_once(
		self,
		mocker: MockerFixture,
		sample_config: Config,
		mock_config_file: None,
	):
		import kdi.util.config

		spy = mocker.spy(kdi.util.config, "load_config")
		assert spy.call_count == 0
		sample_config.get("a")
		assert spy.call_count == 1
		sample_config.get("b")
		assert spy.call_count == 1

	@pytest.mark.parametrize("config_file_data", [{}, {"section": {"a": "first"}}])
	def test_file_missing_keys(
		self,
		mocker: MockerFixture,
		sample_config: Config,
		config_file_data: dict[str, Any],
	):
		mocker.patch("kdi.util.config.read_config_file", return_value=config_file_data)
		with pytest.raises(SystemExit):
			sample_config.load()
