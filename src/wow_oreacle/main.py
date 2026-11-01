import click

from wow_oreacle.mined_ore import MinedOre
from wow_oreacle.mining_run import Competition, MiningRun
from wow_oreacle.persistence.database import SessionLocal, engine
from wow_oreacle.persistence.models import Base
from wow_oreacle.persistence.repository import MiningRunRepository


class OreacleAppError(Exception):
    pass


class OreacleApp:
    def __init__(self, repository: MiningRunRepository):
        self.repository = repository

    def start_mining_run(self, zone: str, route: str) -> MiningRun:
        if self.repository.get_active() is not None:
            raise OreacleAppError("There is already another mining run active.")
        run = MiningRun.start_new(zone=zone, route=route)
        self.repository.save(run)
        return run

    def stop_mining_run(self) -> MiningRun:
        run = self.repository.get_active()

        if run is None:
            raise OreacleAppError("There is no active mining run to stop.")

        run.stop()
        self.repository.save(run)
        return run

    def complete_mining_run(
        self,
        run_id: int,
        ores: list[MinedOre],
        lumber: int,
        competition: Competition,
        comment: str = "",
    ) -> MiningRun:
        run = next(
            (
                run
                for run in self.repository.get_incomplete()
                if run.unique_id == run_id
            ),
            None,
        )

        if run is None:
            raise OreacleAppError(f"No incomplete mining run found with ID {run_id}.")

        run.complete(ores, lumber, competition, comment)
        self.repository.save(run)
        return run

    def get_incomplete_mining_runs(self) -> list[MiningRun]:
        return self.repository.get_incomplete()


def main() -> None:
    from wow_oreacle.cli import cli

    Base.metadata.create_all(engine)

    with SessionLocal() as session:
        repository = MiningRunRepository(session)
        app = OreacleApp(repository=repository)

        try:
            cli(obj={"app": app, "commit": session.commit}, standalone_mode=False)
        except click.ClickException as exc:
            exc.show()
            raise SystemExit(exc.exit_code) from None
        except click.Abort:
            click.echo("\nAborted!", err=True)
            raise SystemExit(1) from None

        session.commit()
