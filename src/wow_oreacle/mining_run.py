import datetime as dt
from dataclasses import dataclass
from enum import Enum, auto
from wow_oreacle.mined_ore import MinedOre


class Status(Enum):
    ACTIVE = auto()
    INCOMPLETE = auto()
    COMPLETED = auto()


class MiningRunError(ValueError):
    pass


@dataclass
class MiningRun:
    """Class for keeping track of mining run statistics."""

    unique_id: str
    zone: str
    route: str
    start_time: dt.datetime
    end_time: dt.datetime | None = None
    ores: list[MinedOre] | None = None
    lumber: int | None = None
    competition: str | None = None
    comment: str | None = None
    status: Status = Status.ACTIVE

    def duration_in_hours(self) -> float:
        # end_time should not be None when status is not ACTIVE
        if self.end_time:
            delta = self.end_time - self.start_time
            return delta.total_seconds() / 3600
        raise MiningRunError(
            "Error: duration_in_hours unknown - Mining run is still active."
        )

    def total_ore(self) -> int:
        if self.status == Status.COMPLETED:
            ore_sum = 0
            if self.ores:
                for ore in self.ores:
                    ore_sum += ore.amount
            return ore_sum
        raise MiningRunError("Error: total_ore unknown - Mining run not complete yet.")

    def ore_per_hour(self) -> float:
        if self.status == Status.COMPLETED:
            return self.total_ore() / self.duration_in_hours()
        raise MiningRunError(
            "Error: ore_per_hour unknown - Mining run not complete yet."
        )
