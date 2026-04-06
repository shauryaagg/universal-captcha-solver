"""CLI application using Typer."""

import typer

app = typer.Typer(
    name="captcha-solver",
    help="Universal Captcha Solver CLI",
    no_args_is_help=True,
)


@app.command()
def version() -> None:
    """Print the current version."""
    from captcha_solver import __version__

    typer.echo(f"captcha-solver {__version__}")
