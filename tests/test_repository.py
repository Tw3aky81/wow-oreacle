import unittest
from datetime import timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from wow_oreacle.mining_run import MiningRun
from wow_oreacle.persistence.models import Base, MinedOreRecord, MiningRunRecord
from wow_oreacle.persistence.repository import MiningRunRepository


class TestRepository(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(self.engine)

        self.session = Session(self.engine)

        self.repository = MiningRunRepository(self.session)

    def tearDown(self) -> None:
        self.session.close()
        self.engine.dispose()

    def make_new_mining_run(self) -> MiningRun:
        return MiningRun.start_new(zone="Eversong Woods", route="Mining Only")

    def test_mining_run_repository_save_new(self):
        run = self.make_new_mining_run()
        self.repository.save(run)

        self.assertIsNotNone(run.unique_id)

        self.session.commit()
        self.session.expunge_all()
        record = self.session.get(MiningRunRecord, run.unique_id)

        assert record is not None
        self.assertEqual(record.zone, run.zone)
        self.assertEqual(record.route, run.route)
        self.assertEqual(record.start_time.replace(tzinfo=timezone.utc), run.start_time)
        self.assertEqual(record.status, run.status)

        self.assertIsNone(record.end_time)
        self.assertIsNone(record.lumber)
        self.assertIsNone(record.competition)
        self.assertIsNone(record.comment)
        self.assertEqual(record.ores, [])
