#!/usr/bin/env bash

uv run ruff format src
uv run ruff check src --fix
