from __future__ import annotations

from typing import TYPE_CHECKING

import click

from wow_oreacle.main import OreacleAppError
from wow_oreacle.mined_ore import MinedOre, OreQuality, OreType
from wow_oreacle.mining_run import Competition, MiningRun

if TYPE_CHECKING:
    from wow_oreacle.main import OreacleApp


@click.group()
def cli():
    """World of Warcraft mining tracker."""
    pass


@cli.command()
@click.pass_obj
def stats(context):
    """Show statistics."""

    app: OreacleApp = context["app"]

    stats = app.get_stats()

    click.echo("=" * 80)
    click.echo("WoW Oreacle")
    click.echo("=" * 80)
    click.echo()
    click.echo("Overall Statistics:")
    click.echo()
    click.echo(f"Completed runs............: {stats['completed_runs']}")
    click.echo(f"Total mining time.........: {stats['total_hours']:.2f} hours")
    click.echo(f"Total ores mined..........: {stats['total_ores']}")
    click.echo(f"Ores/hour.................: {stats['ores_per_hour']:.2f}")
    click.echo(f"Total lumber gathered.....: {stats['total_lumber']}")
    click.echo(f"Lumber/hour...............: {stats['lumber_per_hour']:.2f}")
    click.echo()
    click.echo("-" * 80)


@cli.group()
def miningrun():
    """Manage mining runs."""
    pass


@miningrun.command()
@click.option("--zone", prompt="Zone", help="The zone which you'll mine in.")
@click.option("--route", prompt="Route", help="The route you pick to run.")
@click.pass_obj
def start(context, zone: str, route: str):
    """Start a new mining run."""

    app = context["app"]

    try:
        run = app.start_mining_run(zone, route)
    except OreacleAppError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"Mining run started in {run.zone}")
    click.echo(f"Started at: {run.start_time.astimezone():%Y-%m-%d %H:%M:%S %Z}")


@miningrun.command()
@click.pass_obj
def stop(context):
    """Stop the active mining run."""

    app: OreacleApp = context["app"]
    commit = context["commit"]

    try:
        run = app.stop_mining_run()
    except OreacleAppError as exc:
        raise click.ClickException(str(exc)) from exc

    commit()
    assert run.unique_id is not None
    assert run.end_time is not None

    click.echo("Mining run stopped.")
    click.echo(f"Stopped at: {run.end_time.astimezone():%Y-%m-%d %H:%M:%S %Z}")

    ores, lumber, competition, comment = prompt_mining_results()

    try:
        completed_run = app.complete_mining_run(
            run.unique_id, ores, lumber, competition, comment
        )
    except OreacleAppError as exc:
        raise click.ClickException(str(exc)) from exc

    print_completed_run_stats(completed_run)


@miningrun.command()
@click.pass_obj
def complete(context):
    """Complete an unfinished mining run."""

    app: OreacleApp = context["app"]

    incomplete_runs = app.get_incomplete_mining_runs()

    if len(incomplete_runs) == 0:
        click.echo("There are no unfinished mining runs to complete.")
        return

    click.echo("Incomplete mining runs:")
    click.echo()

    for index, run in enumerate(incomplete_runs, start=1):
        assert run.end_time is not None
        click.echo(
            f"\t{index}. {run.end_time.astimezone():%Y-%m-%d %H:%M}  {run.zone} - {run.route}"
        )

    click.echo()
    selection = click.prompt(
        "Select mining run",
        type=click.IntRange(min=1, max=len(incomplete_runs)),
        default=1,
    )
    selected_run = incomplete_runs[selection - 1]
    assert selected_run.unique_id is not None
    ores, lumber, competition, comment = prompt_mining_results()

    try:
        completed_run = app.complete_mining_run(
            selected_run.unique_id, ores, lumber, competition, comment
        )
    except OreacleAppError as exc:
        raise click.ClickException(str(exc)) from exc

    print_completed_run_stats(completed_run)


def prompt_mining_results():
    click.echo()
    click.echo("Enter your mining results:")

    ores = prompt_mined_ores()
    lumber = click.prompt("Lumber", type=click.IntRange(min=0), default=0)
    competition = prompt_competition()
    comment = click.prompt("Comment", type=str, default="")

    return ores, lumber, competition, comment


def prompt_mined_ores() -> list[MinedOre]:
    ores = []

    for ore_type in OreType:
        for quality in OreQuality:
            amount = click.prompt(
                f"{ore_type.name.title()} ({quality.name.title()})",
                type=click.IntRange(min=0),
                default=0,
            )

            ores.append(
                MinedOre(
                    type=ore_type,
                    quality=quality,
                    amount=amount,
                )
            )

    return ores


def prompt_competition() -> Competition:
    choices = {
        "N": Competition.NONE,
        "L": Competition.LOW,
        "M": Competition.MEDIUM,
        "H": Competition.HIGH,
    }

    answer = click.prompt(
        "Competition (N=None, L=Low, M=Medium, H=High)",
        type=click.Choice(list(choices), case_sensitive=False),
        default="M",
        show_choices=False,
    )

    return choices[answer.upper()]


def print_completed_run_stats(completed_run: MiningRun):
    click.echo(f"\nMining run with ID {completed_run.unique_id} completed.")
    click.echo(f"  Duration: {completed_run.duration_in_hours():.2f} hours")
    click.echo(f"  Total ores: {completed_run.total_ore()}")
    click.echo(f"  Ores per hour: {completed_run.ore_per_hour():.2f}")
    click.echo()
    click.echo(f"  Total lumber: {completed_run.total_lumber()}")
    click.echo(f"  Lumber per hour: {completed_run.lumber_per_hour():.2f}")
