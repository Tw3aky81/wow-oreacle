from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from wow_oreacle.mined_ore import OreQuality, OreType
from wow_oreacle.mining_run import Competition, Status


class Base(DeclarativeBase):
    pass


class MiningRunRecord(Base):
    __tablename__ = "mining_run"

    id: Mapped[int] = mapped_column(primary_key=True)
    zone: Mapped[str]
    route: Mapped[str]
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[Status]
    lumber: Mapped[Optional[int]]
    competition: Mapped[Optional[Competition]]
    comment: Mapped[Optional[str]]

    ores: Mapped[list["MinedOreRecord"]] = relationship(back_populates="mining_run")


class MinedOreRecord(Base):
    __tablename__ = "mined_ores"

    id: Mapped[int] = mapped_column(primary_key=True)
    mining_run_id: Mapped[int] = mapped_column(ForeignKey("mining_run.id"))
    ore_type: Mapped[OreType]
    quality: Mapped[OreQuality]
    amount: Mapped[int]

    mining_run: Mapped["MiningRunRecord"] = relationship(back_populates="ores")
