#!/bin/bash

export POETRY_VIRTUALENVS_IN_PROJECT=true
poetry_version="1.6.1"

# Allows exit with one KeyboardInterrupt
trap "exit 0" SIGINT

# Loads environment variables from .env file
set -a # automatically export all variables
source .env > /dev/null 2>&1
set +a

python3 -m venv .venv
.venv/bin/pip3 install -U pip setuptools
.venv/bin/pip3 install poetry==$poetry_version
yes | .venv/bin/poetry cache clear PyPI --all
yes | .venv/bin/poetry cache clear _default_cache --all

# uncomment if problem with poetry.lock file
# .venv/bin/poetry lock --no-update

.venv/bin/poetry install

.venv/bin/poetry run prisma db push --schema prisma/schema.prisma || exit 1

.venv/bin/poetry run .venv/bin/gunicorn