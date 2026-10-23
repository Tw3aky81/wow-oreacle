from datetime import datetime
from typing import List, Optional
from sqlalchemy import DateTime, String, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class MiningRunRecord(Base):
    __tablename__ = "mining_run"

    id: Mapped[int] = mapped_column(primary_key=True)
    zone: Mapped[str]
    route: Mapped[str]
    start_time: Mapped[datetime] = mapped_column(DateTime)
    end_time: Mapped[Optional[datetime]]
