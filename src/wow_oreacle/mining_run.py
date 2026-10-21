import datetime as dt
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Self

from wow_oreacle.mined_ore import MinedOre


class Status(Enum):
    ACTIVE = auto()
    INCOMPLETE = auto()
    COMPLETED = auto()


class Competition(Enum):
    NONE = auto()
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()


class MiningRunError(ValueError):
    pass


@dataclass
class MiningRun:
    """Class for keeping track of mining run statistics."""

    unique_id: int | None
    zone: str
    route: str
    start_time: dt.datetime
    end_time: dt.datetime | None = None
    ores: list[MinedOre] | None = None
    lumber: int | None = None
    competition: Competition | None = None
    comment: str | None = None
    _status: Status = field(default=Status.ACTIVE, init=False)

    @classmethod
    def start_new(cls, zone: str, route: str) -> Self:
        return cls(
            unique_id=None,
            zone=zone,
            route=route,
            start_time=dt.datetime.now(dt.timezone.utc),
        )

    @property
    def status(self) -> Status:
        return self._status

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

    def stop(self):
        if self._status != Status.ACTIVE:
            raise MiningRunError("Error: Mining run is not in ACTIVE state.")

        end_time = dt.datetime.now(dt.timezone.utc)
        if self.start_time < end_time:
            self.end_time = end_time
            self._status = Status.INCOMPLETE
            return
        raise MiningRunError(
            "Error: 'end_time' cannot be less than or equal to 'start_time'."
        )
