#!/usr/bin/env python
import subprocess
import typer

app = typer.Typer()


@app.command()
def fmt() -> None:
    subprocess.run(["ruff", "format", "."])


@app.command()
def lint() -> None:
    subprocess.run(["mypy", "."])
    subprocess.run(["ruff", "check", "."])
    subprocess.run(["ruff", "format", "--check", "."])


@app.command()
def test() -> None:
    subprocess.run(["pytest"])


@app.command()
def prepare() -> None:
    fmt()
    lint()
    test()


if __name__ == "__main__":
    app()
