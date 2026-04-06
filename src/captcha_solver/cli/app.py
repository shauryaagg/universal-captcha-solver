"""CLI application for captcha-solver."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="captcha-solver",
    help="Universal Captcha Solver - solve any captcha from the command line.",
    no_args_is_help=True,
)
console = Console()


def version_callback(value: bool) -> None:
    if value:
        from captcha_solver import __version__

        console.print(f"captcha-solver v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """Universal Captcha Solver CLI."""


@app.command()
def solve(
    image_path: str = typer.Argument(..., help="Path to captcha image file."),
    captcha_type: Optional[str] = typer.Option(
        None,
        "--type",
        "-t",
        help="Captcha type (text, slider, math, etc). Auto-detects if omitted.",
    ),
    output: str = typer.Option("text", "--output", "-o", help="Output format: text or json."),
    backend: Optional[str] = typer.Option(
        None, "--backend", "-b", help="Model backend: local or cloud."
    ),
) -> None:
    """Solve a captcha image."""
    path = Path(image_path)
    if not path.exists():
        console.print(f"[red]Error:[/red] File not found: {image_path}")
        raise typer.Exit(code=1)

    try:
        from captcha_solver.config import Settings
        from captcha_solver.core.pipeline import SolverPipeline

        settings_kwargs: dict[str, str] = {}
        if backend:
            settings_kwargs["model_backend"] = backend
        settings = Settings(**settings_kwargs)
        pipeline = SolverPipeline(settings=settings)

        result = pipeline.solve(image=path, captcha_type=captcha_type)

        if output == "json":
            console.print(json.dumps(result.to_dict(), indent=2))
        else:
            if result.confidence >= 0.8:
                confidence_color = "green"
            elif result.confidence >= 0.5:
                confidence_color = "yellow"
            else:
                confidence_color = "red"
            console.print(
                f"Solution: [bold]{result.solution}[/bold]  "
                f"(type: {result.captcha_type}, "
                f"confidence: [{confidence_color}]{result.confidence:.2f}[/{confidence_color}], "
                f"{result.elapsed_ms:.0f}ms)"
            )
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)


@app.command()
def detect(
    image_path: str = typer.Argument(..., help="Path to captcha image file."),
    output: str = typer.Option("text", "--output", "-o", help="Output format: text or json."),
) -> None:
    """Detect captcha type from image."""
    path = Path(image_path)
    if not path.exists():
        console.print(f"[red]Error:[/red] File not found: {image_path}")
        raise typer.Exit(code=1)

    try:
        from captcha_solver.core.pipeline import get_default_pipeline

        pipeline = get_default_pipeline()
        captcha_type, confidence = pipeline.detect(path)

        if output == "json":
            console.print(
                json.dumps({"captcha_type": captcha_type.value, "confidence": confidence})
            )
        else:
            console.print(
                f"Detected: [bold]{captcha_type.value}[/bold] (confidence: {confidence:.2f})"
            )
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Server host."),
    port: int = typer.Option(8000, "--port", "-p", help="Server port."),
    workers: int = typer.Option(1, "--workers", "-w", help="Number of workers."),
) -> None:
    """Start the REST API server."""
    try:
        import uvicorn
    except ImportError:
        console.print(
            "[red]Error:[/red] Server dependencies not installed. "
            "Run: pip install universal-captcha-solver[server]"
        )
        raise typer.Exit(code=1)

    console.print(f"Starting captcha-solver server on [bold]http://{host}:{port}[/bold]")
    console.print("API docs available at /docs")
    uvicorn.run(
        "captcha_solver.server.app:app",
        host=host,
        port=port,
        workers=workers,
    )


# Models subcommand
models_app = typer.Typer(help="Manage captcha solver models.")
app.add_typer(models_app, name="models")


@models_app.command("list")
def models_list() -> None:
    """List available models."""
    from captcha_solver.models.manager import ModelManager

    manager = ModelManager()
    available = manager.list_available()
    downloaded = {m.name for m in manager.list_downloaded()}

    table = Table(title="Available Models")
    table.add_column("Name", style="bold")
    table.add_column("Size")
    table.add_column("Status")
    table.add_column("Description")

    for model in available:
        size_mb = f"{model.size_bytes / 1_000_000:.1f}MB"
        if model.name in downloaded:
            status = "[green]downloaded[/green]"
        else:
            status = "[dim]not downloaded[/dim]"
        table.add_row(model.name, size_mb, status, model.description)

    console.print(table)


@models_app.command("download")
def models_download(
    name: str = typer.Argument(..., help="Model name to download."),
) -> None:
    """Download a model."""
    from captcha_solver.models.manager import ModelManager

    manager = ModelManager()
    try:
        path = manager.download_model(name)
        console.print(f"[green]Downloaded[/green] {name} to {path}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)
