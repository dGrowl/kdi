from pathlib import Path
import logging


def get_log_path():
	p = Path(__file__).parents[3] / "logs" / "last_run.txt"
	return p.absolute()


logging.basicConfig(
	filename=get_log_path(),
	filemode="w",
	format="%(asctime)s - %(levelname)s: %(message)s",
	level=logging.DEBUG,
)
log = logging.getLogger("kdi")
