from datetime import datetime, timezone
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from wow_oreacle.mined_ore import OreQuality, OreType
from wow_oreacle.mining_run import Status
from wow_oreacle.persistence.models import Base, MinedOreRecord, MiningRunRecord


class TestModels(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(self.engine)

        self.session = Session(self.engine)

    def tearDown(self) -> None:
        self.session.close()
        self.engine.dispose()

    def make_test_mining_run_record(self) -> MiningRunRecord:
        return MiningRunRecord(
            zone="Eversong Woods",
            route="Mining only",
            start_time=datetime(2026, 10, 20, tzinfo=timezone.utc),
            status=Status.ACTIVE,
        )

    def make_test_mined_ore_records(self) -> list[MinedOreRecord]:
        return [
            MinedOreRecord(
                ore_type=OreType.COPPER,
                quality=OreQuality.BRONZE,
                amount=10,
            ),
            MinedOreRecord(
                ore_type=OreType.TIN,
                quality=OreQuality.GOLD,
                amount=25,
            ),
        ]

    def test_mining_run_record_roundtrip(self):
        record = self.make_test_mining_run_record()
        self.session.add(record)
        self.session.commit()

        record_id = record.id
        self.session.expunge_all()

        loaded = self.session.get(MiningRunRecord, record_id)

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.zone, "Eversong Woods")  # pyright: ignore[reportOptionalMemberAccess]
        self.assertEqual(loaded.status, Status.ACTIVE)  # pyright: ignore[reportOptionalMemberAccess]

    def test_mining_run_record_relationship(self):
        record = self.make_test_mining_run_record()
        record.ores = self.make_test_mined_ore_records()
        self.session.add(record)
        self.session.commit()

        record_id = record.id
        self.session.expunge_all()

        loaded = self.session.get(MiningRunRecord, record_id)

        self.assertIsNotNone(loaded)

        expected = [
            (OreType.COPPER, OreQuality.BRONZE, 10),
            (OreType.TIN, OreQuality.GOLD, 25),
        ]

        actual = [
            (ore.ore_type, ore.quality, ore.amount)
            for ore in loaded.ores  # pyright: ignore
        ]

        self.assertCountEqual(actual, expected)

    def test_mining_run_record_datetime_timezone(self):
        record = self.make_test_mining_run_record()
        self.session.add(record)
        self.session.commit()

        record_id = record.id
        self.session.expunge_all()

        loaded = self.session.get(MiningRunRecord, record_id)

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.start_time, datetime(2026, 10, 20))  # pyright: ignore[reportOptionalMemberAccess]
