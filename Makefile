VENV ?= .venv
PYTHON_VERSION ?= 3.13

.PHONY: init clean pretty lint mypy ruff-lint test test-cov

.create-venv:
	test -d $(VENV) || python$(PYTHON_VERSION) -m venv $(VENV)
	$(VENV)/bin/python -m pip install --upgrade pip
	$(VENV)/bin/python -m pip install poetry

.install-deps:
	poetry run poetry install

.install-pre-commit:
	poetry run pre-commit install

init:
	@echo "Creating virtual environment..."
	@$(MAKE) .create-venv
	@echo "Installing dependencies..."
	@$(MAKE) .install-deps
	@echo "Installing pre-commit hooks..."
	@$(MAKE) .install-pre-commit

clean:
	rm -rf .venv
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf .mypy_cache
	rm -rf dist
	rm -rf *.egg-info

pretty:
	poetry run ruff check --fix-only .
	poetry run ruff format .

ruff-lint:
	poetry run ruff check .

mypy:
	poetry run mypy --install-types --non-interactive .


lint: ruff-lint mypy

test:
	poetry run pytest ./tests

test-cov:
	poetry run pytest ./tests --cov=python_chat --cov=./tests --cov-report term-missing --cov-fail-under=85
