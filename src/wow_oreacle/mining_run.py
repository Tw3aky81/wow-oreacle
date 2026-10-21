import datetime as dt
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import ClassVar, Self

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

    REQUIRED_ORE_COMBINATIONS: ClassVar[int] = 9

    unique_id: int | None
    zone: str
    route: str
    start_time: dt.datetime
    _end_time: dt.datetime | None = field(default=None, init=False)
    _ores: tuple[MinedOre, ...] | None = field(default=None, init=False)
    _lumber: int | None = field(default=None, init=False)
    _competition: Competition | None = field(default=None, init=False)
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

    @property
    def end_time(self) -> dt.datetime | None:
        return self._end_time

    @property
    def ores(self) -> tuple[MinedOre, ...] | None:
        return self._ores

    @property
    def lumber(self) -> int | None:
        return self._lumber

    @property
    def competition(self) -> Competition | None:
        return self._competition

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
        if not self.status == Status.ACTIVE:
            raise MiningRunError("Error: Mining run is not in ACTIVE state.")

        end_time = dt.datetime.now(dt.timezone.utc)
        if not self.start_time < end_time:
            raise MiningRunError(
                "Error: 'end_time' cannot be less than or equal to 'start_time'."
            )
        self._end_time = end_time
        self._status = Status.INCOMPLETE

    def complete(
        self,
        ores: list[MinedOre],
        lumber: int,
        competition: Competition,
        comment: str = "",
    ):
        if self.status != Status.INCOMPLETE:
            raise MiningRunError("Error: Mining run is not in INCOMPLETE state.")

        if not isinstance(ores, list):
            raise TypeError("Error: ores is not a list")

        if type(lumber) is not int:
            raise TypeError("Error: lumber should be of type 'int'.")

        if not isinstance(competition, Competition):
            raise TypeError("Error: competition is not a valid type.")

        if (
            not all(isinstance(ore, MinedOre) for ore in ores)
            or not len(ores) == self.REQUIRED_ORE_COMBINATIONS
            or not len({(ore.type, ore.quality) for ore in ores})
            == self.REQUIRED_ORE_COMBINATIONS
        ):
            raise MiningRunError("Error: List of ores is not complete or invalid.")

        if lumber < 0:
            raise MiningRunError(
                "Error: Amount of lumber must be bigger or equal to zero."
            )

        self._ores = tuple(ores)
        self._lumber = lumber
        self._competition = competition
        self.comment = comment
        self._status = Status.COMPLETED
