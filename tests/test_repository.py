import unittest
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from wow_oreacle.mined_ore import MinedOre, OreQuality, OreType
from wow_oreacle.mining_run import Competition, MiningRun, Status
from wow_oreacle.persistence.models import Base, MiningRunRecord
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

    def make_test_ores(self) -> list[MinedOre]:
        return [
            MinedOre(OreType.COPPER, OreQuality.BRONZE, 10),
            MinedOre(OreType.COPPER, OreQuality.SILVER, 20),
            MinedOre(OreType.COPPER, OreQuality.GOLD, 30),
            MinedOre(OreType.TIN, OreQuality.BRONZE, 15),
            MinedOre(OreType.TIN, OreQuality.SILVER, 25),
            MinedOre(OreType.TIN, OreQuality.GOLD, 35),
            MinedOre(OreType.SILVER, OreQuality.BRONZE, 18),
            MinedOre(OreType.SILVER, OreQuality.SILVER, 28),
            MinedOre(OreType.SILVER, OreQuality.GOLD, 38),
        ]

    def create_saved_incomplete_run(self) -> MiningRun:
        run = self.make_new_mining_run()
        self.repository.save(run)

        run.stop()
        self.repository.save(run)

        return run

    def create_saved_completed_run(self) -> MiningRun:
        run = self.create_saved_incomplete_run()
        ores = self.make_test_ores()

        run.complete(ores=ores, lumber=100, competition=Competition.LOW)
        self.repository.save(run)

        return run

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

    def test_mining_run_repository_get_active(self):
        record = self.repository.get_active()
        self.assertIsNone(record)

        saved_run = self.make_new_mining_run()
        self.repository.save(saved_run)

        self.session.commit()
        self.session.expunge_all()

        loaded_run = self.repository.get_active()
        assert loaded_run is not None
        self.assertIsInstance(loaded_run, MiningRun)
        self.assertEqual(loaded_run.status, Status.ACTIVE)
        self.assertEqual(loaded_run.unique_id, saved_run.unique_id)

    def test_mining_run_repository_save_incomplete(self):
        run = self.create_saved_incomplete_run()

        self.session.commit()
        self.session.expunge_all()

        record = self.session.get(MiningRunRecord, run.unique_id)
        assert record is not None
        self.assertEqual(record.status, Status.INCOMPLETE)
        self.assertIsNotNone(record.end_time)
        self.assertIsInstance(record.end_time, datetime)

    def test_mining_run_repository_save_completed(self):
        run = self.create_saved_completed_run()

        self.session.commit()
        self.session.expunge_all()

        record = self.session.get(MiningRunRecord, run.unique_id)
        assert record is not None
        self.assertEqual(record.status, Status.COMPLETED)
        self.assertEqual(record.lumber, 100)
        self.assertEqual(record.competition, Competition.LOW)
        self.assertEqual(record.comment, "")

        actual = [(ore.ore_type, ore.quality, ore.amount) for ore in record.ores]
        expected = [
            (ore.type, ore.quality, ore.amount) for ore in self.make_test_ores()
        ]
        self.assertCountEqual(actual, expected)

    def test_mining_run_repository_save_completed_again(self):
        run = self.create_saved_completed_run()

        run.comment = "Updated comment"
        self.repository.save(run)

        self.session.commit()
        self.session.expunge_all()

        record = self.session.get(MiningRunRecord, run.unique_id)
        assert record is not None
        self.assertEqual(record.comment, "Updated comment")
        self.assertEqual(len(record.ores), 9)

    def test_mining_run_repository_get_imcomplete(self):
        self.assertEqual(self.repository.get_incomplete(), [])

        self.make_new_mining_run()
        self.create_saved_incomplete_run()
        self.create_saved_incomplete_run()
        self.create_saved_completed_run()

        self.session.commit()
        self.session.expunge_all()

        runs = self.repository.get_incomplete()

        self.assertEqual(len(runs), 2)
        self.assertTrue(all(run.status == Status.INCOMPLETE for run in runs))

    def test_mining_run_repository_get_completed(self):
        self.assertEqual(self.repository.get_completed(), [])

        self.make_new_mining_run()
        self.create_saved_incomplete_run()
        self.create_saved_completed_run()
        self.create_saved_completed_run()

        self.session.commit()
        self.session.expunge_all()

        runs = self.repository.get_completed()

        self.assertEqual(len(runs), 2)
        self.assertTrue(all(run.status == Status.COMPLETED for run in runs))
