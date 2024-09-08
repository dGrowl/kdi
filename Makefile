PY_DIRS = src tests dev

format:
	ruff format $(PY_DIRS)

lint:
	ruff check $(PY_DIRS)

test:
	pytest -vx

dev:
	python -m kdi

prod:
	python -OO -m kdi
