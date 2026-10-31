from __future__ import annotations

from typing import TYPE_CHECKING

import click

from wow_oreacle.main import OreacleAppError
from wow_oreacle.mined_ore import MinedOre, OreQuality, OreType
from wow_oreacle.mining_run import Competition

if TYPE_CHECKING:
    from wow_oreacle.main import OreacleApp


@click.group()
def cli():
    """World of Warcraft mining tracker."""
    pass


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

    run = app.start_mining_run(zone, route)
    click.echo(f"Mining run started in {run.zone}")
    click.echo(f"Started at: {run.start_time}")


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

    click.echo("Mining run stopped.")
    click.echo()
    click.echo("Enter your mining results:")

    ores = prompt_mined_ores()
    lumber = click.prompt("Lumber", type=click.IntRange(min=0), default=0)
    competition = prompt_competition()
    comment = click.prompt("Comment", type=str, default="")

    try:
        app.complete_mining_run(run.unique_id, ores, lumber, competition, comment)
    except OreacleAppError as exc:
        raise click.ClickException(str(exc)) from exc


@miningrun.command()
def complete():
    """Complete an unfinished mining run."""
    ...


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
    )

    return choices[answer.upper()]
