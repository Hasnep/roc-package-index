help:
    @just --list

fix:
    ruff format
    ssort downloader
    ruff check --fix

check:
    ruff format --check
    ssort --check downloader
    ruff check
    basedpyright

run:
    python3 -m downloader

ratchet:
    ratchet upgrade .github/workflows/*.yaml
