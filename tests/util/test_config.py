from pytest_mock import MockerFixture
import pytest

from kdi.util import get_config_value


class TestConfig:
	@pytest.fixture(autouse=True)
	def clear_config_file_data(self, mocker: MockerFixture):
		mocker.patch("kdi.util.config.config_file_data", None)

	@pytest.fixture
	def mock_config_file(self, mocker: MockerFixture):
		mocker.patch(
			"kdi.util.config.read_config_file",
			return_value={"section": {"a": "first", "b": "second"}},
		)

	def test_loads_keys(self, mock_config_file: None):
		assert get_config_value("section", "a") == "first"
		assert get_config_value("section", "b") == "second"

	def test_reads_file_once(self, mocker: MockerFixture, mock_config_file: None):
		import kdi.util.config

		config_loader = mocker.spy(kdi.util.config, "load_config")
		config_loader.assert_not_called()
		get_config_value("section", "a")
		config_loader.assert_called_once()
		get_config_value("section", "b")
		config_loader.assert_called_once()

	def test_missing_table_key(self):
		with pytest.raises(SystemExit):
			get_config_value("section_two", "a")

	def test_missing_key(self):
		with pytest.raises(SystemExit):
			get_config_value("section", "c")
