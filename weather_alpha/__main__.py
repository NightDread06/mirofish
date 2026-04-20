"""Allows `python -m weather_alpha ...` to route through the Typer CLI."""

from .cli import app

if __name__ == "__main__":
    app()
