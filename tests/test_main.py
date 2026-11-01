import datetime as dt
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from wow_oreacle.main import OreacleApp, OreacleAppError
from wow_oreacle.mined_ore import MinedOre, OreQuality, OreType
from wow_oreacle.mining_run import Competition, MiningRun, Status
from wow_oreacle.persistence.models import Base, MiningRunRecord
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

    def make_test_ores(self, *amounts: int) -> list[MinedOre]:
        assert len(amounts) == 9

        return [
            MinedOre(ore_type, quality, amount)
            for (ore_type, quality), amount in zip(
                ((ore_type, quality) for ore_type in OreType for quality in OreQuality),
                amounts,
                strict=True,
            )
        ]

    def make_active_run(self, zone: str, route: str) -> MiningRun:
        run = self.app.start_mining_run(zone, route)
        self.session.commit()
        return run

    def make_incomplete_run(self, zone: str, route: str) -> tuple[MiningRun, MiningRun]:
        active_run = self.make_active_run(zone, route)
        stopped_run = self.app.stop_mining_run()
        self.session.commit()
        return active_run, stopped_run

    def make_completed_run(
        self,
        zone: str,
        route: str,
        ores: list[MinedOre],
        lumber: int,
        competition: Competition,
        comment: str,
    ) -> tuple[MiningRun, MiningRun, MiningRun]:
        initial_run, stopped_run = self.make_incomplete_run(zone, route)

        assert stopped_run.unique_id is not None

        completed_run = self.app.complete_mining_run(
            run_id=stopped_run.unique_id,
            ores=ores,
            lumber=lumber,
            competition=competition,
            comment=comment,
        )
        self.session.commit()
        return initial_run, stopped_run, completed_run

    def restore_complete_run_with_duration(
        self,
        duration_hours: float,
        ores: list[MinedOre],
        lumber: int = 0,
        zone: str = "Eversong Woods",
        route: str = "Mining only",
        competition: Competition = Competition.NONE,
        comment: str = "",
    ) -> MiningRun:
        new_run = self.app.start_mining_run(zone, route)
        self.session.commit()
        assert new_run.unique_id is not None

        start_time = dt.datetime(2026, 1, 1, 12, 0, tzinfo=dt.timezone.utc)
        end_time = start_time + dt.timedelta(hours=duration_hours)

        record = self.session.get(MiningRunRecord, new_run.unique_id)
        assert record is not None
        record.start_time = start_time
        self.session.flush()

        run = MiningRun.restore(
            new_run.unique_id,
            zone,
            route,
            start_time,
            end_time,
            Status.COMPLETED,
            tuple(ores),
            lumber,
            competition,
            comment,
        )

        self.repository.save(run)
        self.session.commit()

        return run

    def test_oreacle_app_start_mining_run(self):
        run = self.make_active_run("Eversong Woods", "Mining Only")

        self.assertEqual(run.status, Status.ACTIVE)
        self.assertIsNotNone(run.unique_id)

        self.session.expunge_all()

        loaded_run = self.repository.get_active()
        assert loaded_run is not None
        self.assertEqual(loaded_run.unique_id, run.unique_id)

    def test_oreacle_app_start_mining_run_already_active(self):
        self.make_active_run("Eversong Woods", "Mining Only")
        with self.assertRaises(OreacleAppError):
            self.app.start_mining_run("Elwynn Forest", "Route A")

    def test_oreacle_app_stop_mining_run(self):
        initial_run, stopped_run = self.make_incomplete_run(
            "Eversong Woods", "Mining Only"
        )

        self.assertEqual(stopped_run.status, Status.INCOMPLETE)
        self.assertEqual(initial_run.unique_id, stopped_run.unique_id)

    def test_oreacle_app_stop_mining_run_none_active(self):
        with self.assertRaises(OreacleAppError):
            self.app.stop_mining_run()

    def test_oreacle_app_complete_mining_run(self):
        ores = self.make_test_ores(0, 13, 4, 0, 12, 5, 0, 8, 2)
        initial_run, _, completed_run = self.make_completed_run(
            "Eversong Woods",
            "Mining Only",
            ores,
            100,
            Competition.LOW,
            "No fishing along the way.",
        )
        self.assertEqual(completed_run.status, Status.COMPLETED)
        self.assertEqual(initial_run.unique_id, completed_run.unique_id)

        assert completed_run.ores is not None
        self.assertCountEqual(completed_run.ores, tuple(ores))
        self.assertEqual(completed_run.lumber, 100)
        self.assertEqual(completed_run.competition, Competition.LOW)
        self.assertEqual(completed_run.comment, "No fishing along the way.")

    def test_oreacle_app_complete_mining_run_non_existing(self):
        non_existing_id = 49
        ores = self.make_test_ores(0, 13, 4, 0, 12, 5, 0, 8, 2)

        with self.assertRaises(OreacleAppError):
            self.app.complete_mining_run(
                run_id=non_existing_id,
                ores=ores,
                lumber=100,
                competition=Competition.LOW,
                comment="No fishing along the way.",
            )

    def test_oreacle_app_get_incomplete(self):
        incomplete_runs = []

        for i in range(2):
            _, run = self.make_incomplete_run("Eversong Woods", "Mining Only")
            incomplete_runs.append(run)

        loaded_runs = self.app.get_incomplete_mining_runs()
        self.assertCountEqual(loaded_runs, incomplete_runs)

    def test_oreacle_app_get_stats(self):
        self.restore_complete_run_with_duration(
            duration_hours=1.0,
            ores=self.make_test_ores(0, 10, 5, 0, 15, 10, 0, 20, 5),
            lumber=50,
        )

        self.restore_complete_run_with_duration(
            duration_hours=2.0,
            ores=self.make_test_ores(0, 35, 25, 0, 10, 5, 0, 15, 15),
            lumber=90,
        )

        stats = self.app.get_stats()

        self.assertEqual(stats["completed_runs"], 2)
        self.assertEqual(stats["total_hours"], 3.0)
        self.assertEqual(stats["total_ores"], 170)
        self.assertAlmostEqual(stats["ores_per_hour"], 170 / 3)
        self.assertEqual(stats["total_lumber"], 140)
        self.assertAlmostEqual(stats["lumber_per_hour"], 140 / 3)
