import json
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .evaluator import evaluate, validate_resume
from .exceptions import (
    EmptyFileError,
    InvalidResumeError,
    MissingInputError,
    NonEnglishResumeError,
    UnreadableFileError,
)
from .parsers import parse_resume_input

app = typer.Typer(help="TalentScope — AI-powered hiring recommendation tool")
console = Console()
err = Console(stderr=True, style="red")


def _abort(message: str, exit_code: int = 1) -> None:
    err.print(f"[bold]Error:[/bold] {message}")
    raise typer.Exit(exit_code)


def _print_recommendation(rec) -> None:
    color = {"recommend": "green", "hold": "yellow", "reject": "red"}[rec.recommendation]
    console.print(
        Panel(
            f"[bold {color}]{rec.recommendation.upper()}[/bold {color}]",
            title="Recommendation",
            expand=False,
        )
    )

    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_row("Confidence", f"{rec.confidence:.0%}")
    table.add_row("Must-have coverage", f"{rec.must_have_coverage:.0%}")
    if rec.flags:
        table.add_row("Flags", ", ".join(rec.flags))
    console.print(table)

    console.print("\n[bold]Evidence[/bold]")
    for reason in rec.reasons:
        icon = "[green]+[/green]" if reason.signal == "positive" else "[red]![/red]"
        console.print(f"  {icon} [bold]{reason.label}[/bold]")
        console.print(f'      "{reason.evidence}"')


@app.command()
def run(
    jd: Optional[str] = typer.Option(None, "--jd", help="Job description text"),
    jd_file: Optional[Path] = typer.Option(None, "--jd-file", help="Job description file (.txt)"),
    resume: Optional[str] = typer.Option(None, "--resume", help="Resume text"),
    resume_file: Optional[Path] = typer.Option(None, "--resume-file", help="Resume file (.pdf/.docx)"),
    output_json: bool = typer.Option(False, "--json", help="Output raw JSON instead of formatted output"),
) -> None:
    """Evaluate a candidate resume against a job description."""

    # --- resolve JD ---
    if jd_file:
        try:
            job_description = jd_file.read_text(encoding="utf-8").strip()
        except Exception as exc:
            _abort(f"Could not read job description file: {exc}")
    elif jd:
        job_description = jd.strip()
    else:
        job_description = None

    # --- check both inputs present (before any file parsing) ---
    has_jd = bool(job_description)
    has_resume_input = bool(resume or resume_file)

    if not has_jd and not has_resume_input:
        _abort(
            "Both the job description and resume are required. "
            "Please provide a job description (--jd or --jd-file) "
            "and a resume (--resume or --resume-file)."
        )
    if not has_jd:
        _abort("A job description is required. Use --jd or --jd-file.")
    if not has_resume_input:
        _abort("A resume is required. Use --resume or --resume-file.")

    # --- resolve resume (file parsing may trigger HITL) ---
    resume_text = None
    try:
        resume_text = parse_resume_input(resume, resume_file)
    except EmptyFileError as exc:
        _abort(str(exc))
    except UnreadableFileError:
        console.print(
            Panel(
                "The uploaded file could not be read. "
                "This case has been flagged for [bold]human review (HITL)[/bold].\n"
                "Please have a recruiter evaluate this application manually.",
                title="Manual Review Required",
                style="yellow",
            )
        )
        raise typer.Exit(2)

    # --- validate resume ---
    try:
        validate_resume(resume_text)
    except NonEnglishResumeError:
        _abort(
            "The resume does not appear to be in English. "
            "Please provide an English resume."
        )
    except InvalidResumeError as exc:
        _abort(str(exc))

    # --- evaluate ---
    console.print("Evaluating candidate...", style="dim")
    try:
        recommendation = evaluate(job_description, resume_text)
    except Exception as exc:
        _abort(f"Evaluation failed: {exc}")

    if output_json:
        print(recommendation.model_dump_json(indent=2))
    else:
        _print_recommendation(recommendation)
