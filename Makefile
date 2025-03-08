.PHONY: init clean pretty lint mypy

init:
	python3 -m venv .venv
	. .venv/bin/activate && \
	pip install --upgrade pip && \
	pip install poetry && \
	poetry install

clean:
	rm -rf .venv
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf .mypy_cache
	rm -rf dist
	rm -rf *.egg-info

pretty:
	ruff format .
	ruff check --fix --exit-zero .

lint:
	mypy .
	ruff check .

mypy:
	mypy .
