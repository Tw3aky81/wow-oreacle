from sqlalchemy.orm import Session

from wow_oreacle.mining_run import MiningRun
from wow_oreacle.persistence.models import MiningRunRecord


class MiningRunRepositoryError(Exception):
    pass


class MiningRunRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, run: MiningRun) -> None:
        if run is None:
            raise MiningRunRepositoryError(
                "Error: Expected a MiningRun object to save, got None."
            )

        if run.unique_id is None:
            new_record = MiningRunRecord(
                zone=run.zone,
                route=run.route,
                start_time=run.start_time,
                status=run.status,
            )
            self.session.add(new_record)
            self.session.flush()
            run.unique_id = new_record.id

    def get_active(self) -> MiningRun | None:
        raise NotImplementedError

    def get_incomplete(self) -> list[MiningRun]:
        raise NotImplementedError

    def get_completed(self) -> list[MiningRun]:
        raise NotImplementedError
