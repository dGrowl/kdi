from pytest_mock import MockerFixture
import pytest

from kdi.util import get_config_value


@pytest.fixture(autouse=True)
def clear_config_file_data(mocker: MockerFixture):
	mocker.patch("kdi.util.config.config_file_data", None)


@pytest.fixture
def mock_config_file(mocker: MockerFixture):
	mocker.patch(
		"kdi.util.config.read_config_file",
		return_value={"section": {"a": "first", "b": "second"}},
	)


class TestConfig:
	def test_loads_keys(self, mock_config_file: None):
		assert get_config_value("section", "a") == "first"
		assert get_config_value("section", "b") == "second"

	def test_reads_file_once(self, mocker: MockerFixture, mock_config_file: None):
		import kdi.util.config

		spy = mocker.spy(kdi.util.config, "load_config")
		assert spy.call_count == 0
		get_config_value("section", "a")
		assert spy.call_count == 1
		get_config_value("section", "b")
		assert spy.call_count == 1

	def test_missing_table_key(self):
		with pytest.raises(SystemExit):
			get_config_value("section_two", "a")

	def test_missing_key(self):
		with pytest.raises(SystemExit):
			get_config_value("section", "c")
