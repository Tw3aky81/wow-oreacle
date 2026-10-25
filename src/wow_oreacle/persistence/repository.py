from datetime import timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from wow_oreacle.mined_ore import MinedOre
from wow_oreacle.mining_run import MiningRun, Status
from wow_oreacle.persistence.models import MinedOreRecord, MiningRunRecord


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
            new_record.comment = run.comment
            self.session.add(new_record)
            self.session.flush()
            run.unique_id = new_record.id
        else:
            record = self.session.get(MiningRunRecord, run.unique_id)
            if record is None:
                raise MiningRunRepositoryError(
                    f"Mining run with ID {run.unique_id} not found."
                )

            record.status = run.status
            record.end_time = run.end_time
            record.lumber = run.lumber
            record.competition = run.competition
            record.comment = run.comment

            if run.ores is not None:
                record.ores = [
                    MinedOreRecord(
                        ore_type=ore.type,
                        quality=ore.quality,
                        amount=ore.amount,
                    )
                    for ore in run.ores
                ]

    def get_active(self) -> MiningRun | None:
        record = self.session.scalars(
            select(MiningRunRecord).where(MiningRunRecord.status == Status.ACTIVE)
        ).one_or_none()

        if record is None:
            return None

        return self._to_domain(record)

    def get_incomplete(self) -> list[MiningRun]:
        records = self.session.scalars(
            select(MiningRunRecord).where(MiningRunRecord.status == Status.INCOMPLETE)
        ).all()

        return [self._to_domain(record) for record in records]

    def get_completed(self) -> list[MiningRun]:
        records = self.session.scalars(
            select(MiningRunRecord).where(MiningRunRecord.status == Status.COMPLETED)
        ).all()

        return [self._to_domain(record) for record in records]

    def _to_domain(self, record: MiningRunRecord) -> MiningRun:
        ores = (
            tuple(
                MinedOre(
                    type=ore.ore_type,
                    quality=ore.quality,
                    amount=ore.amount,
                )
                for ore in record.ores
            )
            if record.status == Status.COMPLETED
            else None
        )

        return MiningRun.restore(
            unique_id=record.id,
            zone=record.zone,
            route=record.route,
            start_time=record.start_time.replace(tzinfo=timezone.utc),
            end_time=record.end_time,
            status=record.status,
            ores=ores,
            lumber=record.lumber,
            competition=record.competition,
            comment=record.comment,
        )
