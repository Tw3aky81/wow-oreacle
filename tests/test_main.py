import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from wow_oreacle.main import OreacleApp, OreacleAppError
from wow_oreacle.mined_ore import MinedOre, OreQuality, OreType
from wow_oreacle.mining_run import Competition, Status
from wow_oreacle.persistence.models import Base
from wow_oreacle.persistence.repository import MiningRunRepository


class TestOreacleApp(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)

        self.session = Session(self.engine)
        self.repository = MiningRunRepository(self.session)
        self.app = OreacleApp(self.repository)

    def tearDown(self):
        self.session.close()
        self.engine.dispose()

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

    def test_oreacle_app_start_mining_run(self):
        run = self.app.start_mining_run("Eversong Woods", "Mining Only")
        self.session.commit()

        self.assertEqual(run.status, Status.ACTIVE)
        self.assertIsNotNone(run.unique_id)

        self.session.expunge_all()

        loaded_run = self.repository.get_active()
        assert loaded_run is not None
        self.assertEqual(loaded_run.unique_id, run.unique_id)

    def test_oreacle_app_start_mining_run_already_active(self):
        self.app.start_mining_run("Eversong Woods", "Mining Only")
        self.session.commit()

        with self.assertRaises(OreacleAppError):
            self.app.start_mining_run("Elwynn Forest", "Route A")

    def test_oreacle_app_stop_mining_run(self):
        initial_run = self.app.start_mining_run("Eversong Woods", "Mining Only")
        self.session.commit()

        stopped_run = self.app.stop_mining_run()
        self.session.commit()

        self.assertEqual(stopped_run.status, Status.INCOMPLETE)
        self.assertEqual(initial_run.unique_id, stopped_run.unique_id)

    def test_oreacle_app_stop_mining_run_none_active(self):
        with self.assertRaises(OreacleAppError):
            self.app.stop_mining_run()

    def test_oreacle_app_complete_mining_run(self):
        initial_run = self.app.start_mining_run("Eversong Woods", "Mining Only")
        self.session.commit()

        stopped_run = self.app.stop_mining_run()
        self.session.commit()

        assert stopped_run.unique_id is not None
        ores = self.make_test_ores()

        completed_run = self.app.complete_mining_run(
            run_id=stopped_run.unique_id,
            ores=ores,
            lumber=100,
            competition=Competition.LOW,
            comment="No fishing along the way.",
        )
        self.session.commit()

        self.assertEqual(completed_run.status, Status.COMPLETED)
        self.assertEqual(initial_run.unique_id, completed_run.unique_id)

        assert completed_run.ores is not None
        self.assertCountEqual(completed_run.ores, tuple(ores))
        self.assertEqual(completed_run.lumber, 100)
        self.assertEqual(completed_run.competition, Competition.LOW)
        self.assertEqual(completed_run.comment, "No fishing along the way.")

    def test_oreacle_app_complete_mining_run_non_existing(self):
        ores = self.make_test_ores()

        with self.assertRaises(OreacleAppError):
            self.app.complete_mining_run(
                run_id=49,
                ores=ores,
                lumber=100,
                competition=Competition.LOW,
                comment="No fishing along the way.",
            )
