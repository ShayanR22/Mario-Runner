#!/bin/zsh
set -e
cd "$(dirname "$0")"
if ! command -v python3 >/dev/null; then
    echo "Install Python 3.12 from python.org, then open this launcher again."
    read -r "?Press Enter to close."
    exit 1
fi
if [ ! -x .venv/bin/python ]; then
    python3 -m venv .venv
fi
if .venv/bin/python -m pip show pygame >/dev/null 2>&1; then
    .venv/bin/python -m pip uninstall -y pygame
fi
if ! .venv/bin/python -c 'import pygame, moderngl; assert pygame.IS_CE and pygame.version.ver == "2.5.8" and moderngl.__version__ == "5.13.0"' >/dev/null 2>&1; then
    .venv/bin/python -m pip install -r requirements.txt
fi
.venv/bin/python main.py "$@"
