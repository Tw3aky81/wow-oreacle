from enum import Enum, auto
from dataclasses import dataclass


class OreType(Enum):
    COPPER = "Refulgent Coppper"
    TIN = "Umbral Tin"
    SILVER = "Brillian Silver"


class OreQuality(Enum):
    BRONZE = auto()
    SILVER = auto()
    GOLD = auto()


@dataclass(frozen=True)
class MinedOre:
    ore: OreType
    quality: OreQuality
    amount: int

    def __post_init__(self):
        if not isinstance(self.ore, OreType):
            raise TypeError("Error: 'ore' is not an OreType.")
        if not isinstance(self.quality, OreQuality):
            raise TypeError("Error: 'quality' is not an OreQuality.")
        if type(self.amount) is not int:
            raise TypeError("Error: 'amount' must be an integer.")
        if self.amount < 0:
            raise ValueError("Error: 'amount' can not be negative.")
