import click


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
def start(app, zone: str, route: str):
    """Start a new mining run."""

    run = app.start_mining_run(zone, route)
    click.echo(f"Mining run started in {run.zone}")
    click.echo(f"Started at: {run.start_time}")


@miningrun.command()
def stop():
    """Stop the active mining run."""
    ...


@miningrun.command()
def complete():
    """Complete an unfinished mining run."""
    ...
