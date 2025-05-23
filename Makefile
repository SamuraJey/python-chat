VENV ?= .venv
PYTHON_VERSION ?= 3.13

.PHONY: init clean pretty lint mypy

.create-venv:
	test -d $(VENV) || python$(PYTHON_VERSION) -m venv $(VENV)
	$(VENV)/bin/python -m pip install --upgrade pip
	$(VENV)/bin/python -m pip install poetry

.install-deps:
	$(VENV)/bin/poetry install

# .install-pre-commit:
# 	$(VENV)/bin/poetry run pre-commit install

init:
	@echo "Creating virtual environment..."
	@$(MAKE) .create-venv
	@echo "Installing dependencies..."
	@$(MAKE) .install-deps

clean:
	rm -rf .venv
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf .mypy_cache
	rm -rf dist
	rm -rf *.egg-info

pretty:
	$(VENV)/bin/ruff check --fix-only .
	$(VENV)/bin/ruff format .

.ruff-lint:
	$(VENV)/bin/ruff check .

mypy:
	$(VENV)/bin/mypy --install-types --non-interactive .


lint: mypy .ruff-lint