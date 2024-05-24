root := $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

export PYTHONPATH=$(root)


install:
	sudo apt-get update
	sudo apt-get install -y python3-pip

	python3 -m pip install --upgrade pip
	python3 -m pip install '.'

test:
	python3 -m pytest

analyze:
	python3 -m mypy

linter:
	python3 -m ruff check

format:
	python3 -m ruff check --fix sphinx_autotoc tests/*.py
	python3 -m ruff format sphinx_autotoc tests/*.py

format-check: linter
	python3 -m ruff format sphinx_autotoc tests/*.py --check
