from pathlib import Path
import logging


def get_log_path():
	p = Path(__file__).parents[3] / "logs" / "last_run.txt"
	return p.absolute()


LOGGING_LEVEL = logging.DEBUG

log = logging.getLogger("kdi")
log.setLevel(LOGGING_LEVEL)

console_handler = logging.StreamHandler()
console_handler.setLevel(LOGGING_LEVEL)
console_handler.setFormatter(
	logging.Formatter("%(asctime)s - %(levelname)s: %(message)s")
)

log.addHandler(console_handler)
