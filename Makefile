root := $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

export PYTHONPATH=$(root)

prepare:
	sudo apt-get update
	sudo apt-get install -y python3-pip
	python3 -m pip install --upgrade pip

test: prepare
	python3 -m pip install pytest
	python3 -m pip install -r requirements.txt
	python3 -m pytest

analyze: prepare
	python3 -m pip install mypy
	python3 -m mypy

linter: prepare
	python3 -m pip install ruff
	python3 -m ruff check

format: prepare
	python3 -m ruff check --fix sphinx_autotoc tests/*.py
	python3 -m ruff format sphinx_autotoc tests/*.py

format-check: linter
	python3 -m ruff format sphinx_autotoc tests/*.py --check
