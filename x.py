#!/usr/bin/env python
import subprocess
import typer

app = typer.Typer()


@app.command()
def fmt() -> None:
    subprocess.run(["ruff", "format", "."], check=True)


@app.command()
def lint() -> None:
    subprocess.run(["mypy", "."], check=True)
    subprocess.run(["ruff", "check", "."], check=True)
    subprocess.run(["ruff", "format", "--check", "."], check=True)


@app.command()
def test() -> None:
    subprocess.run(["pytest"], check=True)


@app.command()
def prepare() -> None:
    fmt()
    lint()
    test()


if __name__ == "__main__":
    app()
