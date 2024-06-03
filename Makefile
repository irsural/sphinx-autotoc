root := $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

export PYTHONPATH=$(root)

test:
	python3 -m pytest

analyze:
	python3 -m mypy

lint:
	python3 -m ruff check

format:
	python3 -m ruff check --fix sphinx_autotoc tests/*.py
	python3 -m ruff format sphinx_autotoc tests/*.py

format-check: linter
	python3 -m ruff format sphinx_autotoc tests/*.py --check
