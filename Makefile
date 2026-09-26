.DEFAULT_GOAL := help

VENV_DIR := .venv

ifeq ($(OS),Windows_NT)
	VENV_BIN := $(VENV_DIR)/Scripts
	PYTHON := $(VENV_BIN)/python.exe
	INSTALL_UV := powershell -NoProfile -Command "irm https://astral.sh/uv/install.ps1 | iex"
else
	VENV_BIN := $(VENV_DIR)/bin
	PYTHON := $(VENV_BIN)/python
	INSTALL_UV := curl -LsSf https://astral.sh/uv/install.sh | sh
endif

.PHONY: help install run

help: ## Show this help message
	@echo "Available commands:"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ { printf "  make %-10s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

install: ## Set up the venv with uv (installing uv first if missing) and install the pre-commit hooks
	@command -v uv >/dev/null 2>&1 || { \
		echo "uv not found, installing it..."; \
		$(INSTALL_UV); \
		echo "uv installed. If 'make install' fails below with 'command not found', open a new terminal (so PATH picks up uv) and re-run 'make install'."; \
	}
	uv venv $(VENV_DIR)
	uv pip install --python $(PYTHON) -r requirements.txt pre-commit
	$(PYTHON) -m pre_commit install
	@echo "Setup complete."

run: ## Start the eVAS application
	$(PYTHON) eVAS.py
