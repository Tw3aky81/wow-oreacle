from sqlalchemy.orm import Session

from wow_oreacle.mining_run import MiningRun


class MiningRunRepositoryError(Exception):
    pass


class MiningRunRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, run: MiningRun) -> None:
        pass

    def get_active(self) -> MiningRun | None:
        raise NotImplementedError

    def get_incomplete(self) -> list[MiningRun]:
        raise NotImplementedError

    def get_completed(self) -> list[MiningRun]:
        raise NotImplementedError
