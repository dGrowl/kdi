PY_DIRS = src tests dev

format:
	ruff format $(PY_DIRS)

lint:
	ruff check $(PY_DIRS)

test:
	pytest

dev:
	python -m kdi

prod:
	python -OO -m kdi
