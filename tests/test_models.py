from datetime import datetime, timezone
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from wow_oreacle.mining_run import Status
from wow_oreacle.persistence.models import Base, MiningRunRecord


class TestModels(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(self.engine)

        self.session = Session(self.engine)

    def tearDown(self) -> None:
        self.session.close()
        self.engine.dispose()

    def test_mining_run_record_roundtrip(self):
        record = MiningRunRecord(
            zone="Eversong Woods",
            route="Mining only",
            start_time=datetime(2026, 10, 20, tzinfo=timezone.utc),
            status=Status.ACTIVE,
        )

        self.session.add(record)
        self.session.commit()

        record_id = record.id
        self.session.expunge_all()

        loaded = self.session.get(MiningRunRecord, record_id)

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.zone, "Eversong Woods")  # pyright: ignore
        self.assertEqual(loaded.status, Status.ACTIVE)  # pyright: ignore
