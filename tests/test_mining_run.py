import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from wow_oreacle.mined_ore import MinedOre, OreQuality, OreType
from wow_oreacle.mining_run import Competition, MiningRun, MiningRunError, Status


class TestMiningRun(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_start_time = datetime(2026, 10, 20, 12, 0, tzinfo=timezone.utc)
        self.mock_end_time = datetime(2026, 10, 20, 13, 30, tzinfo=timezone.utc)

        self.test_ores = [
            MinedOre(OreType.COPPER, OreQuality.BRONZE, 0),
            MinedOre(OreType.COPPER, OreQuality.SILVER, 10),
            MinedOre(OreType.COPPER, OreQuality.GOLD, 100),
            MinedOre(OreType.TIN, OreQuality.BRONZE, 5),
            MinedOre(OreType.TIN, OreQuality.SILVER, 15),
            MinedOre(OreType.TIN, OreQuality.GOLD, 155),
            MinedOre(OreType.SILVER, OreQuality.BRONZE, 7),
            MinedOre(OreType.SILVER, OreQuality.SILVER, 39),
            MinedOre(OreType.SILVER, OreQuality.GOLD, 26),
        ]

    def make_new_run(self) -> MiningRun:
        with patch("wow_oreacle.mining_run.dt.datetime") as mock_datetime:
            mock_datetime.now.return_value = self.mock_start_time

            run = MiningRun.start_new(zone="Example Zone", route="Example Route")

        return run

    def make_incomplete_run(self) -> MiningRun:
        with patch("wow_oreacle.mining_run.dt.datetime") as mock_datetime:
            mock_datetime.now.return_value = self.mock_start_time

            run = MiningRun.start_new(zone="Example Zone", route="Example Route")

            mock_datetime.now.return_value = self.mock_end_time
            run.stop()

        return run

    def test_mining_run_normal_start_initialization(self):
        run = MiningRun(
            unique_id=1,
            zone="Eversong Woods",
            route="Mining Only",
            start_time=datetime(2026, 9, 22, 22, 45, tzinfo=timezone.utc),
        )

        self.assertEqual(run.unique_id, 1)
        self.assertEqual(run.zone, "Eversong Woods")
        self.assertEqual(run.route, "Mining Only")
        self.assertEqual(
            run.start_time,
            datetime(2026, 9, 22, 22, 45, tzinfo=timezone.utc),
        )
        self.assertEqual(run.status, Status.ACTIVE)

        self.assertIsNone(run.end_time)
        self.assertIsNone(run.ores)
        self.assertIsNone(run.lumber)

    def test_mining_run_status_is_read_only(self):
        run = self.make_new_run()
        with self.assertRaises(AttributeError):
            setattr(run, "status", Status.COMPLETED)

    def test_mining_run_active_duration_in_hours_raises_error(self):
        run = self.make_new_run()
        with self.assertRaises(MiningRunError):
            run.duration_in_hours()

    def test_mining_run_active_ore_per_hour_raises_error(self):
        run = self.make_new_run()
        with self.assertRaises(MiningRunError):
            run.ore_per_hour()

    def test_mining_run_active_total_ore_raises_error(self):
        run = self.make_new_run()
        with self.assertRaises(MiningRunError):
            run.total_ore()

    def test_mining_run_incomplete_duration_in_hours(self):
        run = self.make_incomplete_run()
        self.assertEqual(run.duration_in_hours(), 1.5)

    def test_mining_run_incomplete_ore_per_hour_raises_error(self):
        run = self.make_incomplete_run()
        with self.assertRaises(MiningRunError):
            run.ore_per_hour()

    def test_mining_run_incomplete_total_ore_raises_error(self):
        run = self.make_incomplete_run()
        with self.assertRaises(MiningRunError):
            run.total_ore()

    @patch("wow_oreacle.mining_run.dt.datetime")
    def test_mining_run_start_new(self, mock_datetime):
        mock_datetime.now.return_value = self.mock_start_time
        run = MiningRun.start_new(zone="Example Zone", route="Example Route")
        self.assertEqual(run.status, Status.ACTIVE)
        self.assertEqual(run.start_time, self.mock_start_time)
        mock_datetime.now.assert_called_with(timezone.utc)

    @patch("wow_oreacle.mining_run.dt.datetime")
    def test_mining_run_stop(self, mock_datetime):
        mock_datetime.now.return_value = self.mock_start_time
        run = MiningRun.start_new(zone="Example Zone", route="Example Route")

        mock_datetime.now.return_value = self.mock_end_time
        run.stop()

        self.assertEqual(run.status, Status.INCOMPLETE)
        self.assertEqual(run.end_time, self.mock_end_time)
        mock_datetime.now.assert_called_with(timezone.utc)

    @patch("wow_oreacle.mining_run.dt.datetime")
    def test_mining_run_stop_inactive_raises_error(self, mock_datetime):
        mock_datetime.now.return_value = self.mock_start_time
        run = MiningRun.start_new(zone="Example Zone", route="Example Route")

        mock_datetime.now.return_value = self.mock_end_time
        run.stop()
        original_end_time = run.end_time

        with self.assertRaises(MiningRunError):
            run.stop()

        self.assertEqual(run.status, Status.INCOMPLETE)
        self.assertEqual(run.end_time, original_end_time)
        mock_datetime.now.assert_called_with(timezone.utc)

    @patch("wow_oreacle.mining_run.dt.datetime")
    def test_mining_run_stop_invalid_datetime_raises_error(self, mock_datetime):
        mock_datetime.now.return_value = self.mock_end_time
        run = MiningRun.start_new(zone="Example Zone", route="Example Route")

        mock_datetime.now.return_value = self.mock_start_time
        with self.assertRaises(MiningRunError):
            run.stop()

        self.assertEqual(run.status, Status.ACTIVE)
        self.assertIsNone(run.end_time)
        mock_datetime.now.assert_called_with(timezone.utc)

    @patch("wow_oreacle.mining_run.dt.datetime")
    def test_mining_run_stop_equal_datetime_raises_error(self, mock_datetime):
        mock_datetime.now.return_value = self.mock_start_time
        run = MiningRun.start_new(zone="Example Zone", route="Example Route")

        mock_datetime.now.return_value = self.mock_start_time
        with self.assertRaises(MiningRunError):
            run.stop()

        self.assertEqual(run.status, Status.ACTIVE)
        self.assertIsNone(run.end_time)
        mock_datetime.now.assert_called_with(timezone.utc)

    def test_mining_run_complete(self):
        run = self.make_incomplete_run()
        run.complete(
            self.test_ores,
            lumber=24,
            competition=Competition.LOW,
            comment="Test comment",
        )

        if run.ores is None:
            self.fail("Expected ores to be a list, got None")
        for ore in run.ores:
            self.assertIsInstance(ore, MinedOre)
        self.assertEqual(len(run.ores), 9)
        self.assertEqual(run.lumber, 24)
        self.assertIsInstance(run.competition, Competition)
        self.assertEqual(run.comment, "Test comment")
        self.assertEqual(run.status, Status.COMPLETED)

    def test_mining_run_complete_invalid_lumber_type_raises_error(self):
        run = self.make_incomplete_run()
        with self.assertRaises(TypeError):
            run.complete(
                self.test_ores,
                lumber="34",  # pyright: ignore
                competition=Competition.LOW,
                comment="Test comment",
            )

        self.assertNotEqual(run.status, Status.COMPLETED)
        self.assertIsNone(run.ores)
        self.assertIsNone(run.lumber)
        self.assertIsNone(run.competition)

    def test_mining_run_complete_invalid_competition_type_raises_error(self):
        run = self.make_incomplete_run()
        with self.assertRaises(TypeError):
            run.complete(
                self.test_ores,
                lumber=25,
                competition="not to bad",  # pyright: ignore
                comment="Test comment",
            )

        self.assertNotEqual(run.status, Status.COMPLETED)
        self.assertIsNone(run.ores)
        self.assertIsNone(run.lumber)
        self.assertIsNone(run.competition)

    def test_mining_run_complete_invalid_ores_list_type_raises_error(self):
        run = self.make_incomplete_run()
        test_ores = [
            "Copper of good quality",
            "Some Silver",
            "Some Silver",
            "Some Silver",
            "Some Silver",
            "Some Silver",
            "Some Silver",
            "Some Silver",
            "Some Silver",
        ]

        with self.assertRaises(MiningRunError):
            run.complete(
                test_ores,  # pyright: ignore
                lumber=25,
                competition=Competition.MEDIUM,
                comment="Test comment",
            )

        self.assertNotEqual(run.status, Status.COMPLETED)
        self.assertIsNone(run.ores)
        self.assertIsNone(run.lumber)
        self.assertIsNone(run.competition)

    def test_mining_run_complete_incomplete_ores_list_raises_error(self):
        run = self.make_incomplete_run()
        test_ores = [
            MinedOre(OreType.COPPER, OreQuality.SILVER, 10),
            MinedOre(OreType.COPPER, OreQuality.GOLD, 100),
            MinedOre(OreType.TIN, OreQuality.SILVER, 15),
            MinedOre(OreType.TIN, OreQuality.GOLD, 155),
            MinedOre(OreType.SILVER, OreQuality.BRONZE, 7),
            MinedOre(OreType.SILVER, OreQuality.GOLD, 26),
        ]

        with self.assertRaises(MiningRunError):
            run.complete(
                test_ores,
                lumber=25,
                competition=Competition.MEDIUM,
                comment="Test comment",
            )

        self.assertNotEqual(run.status, Status.COMPLETED)
        self.assertIsNone(run.ores)
        self.assertIsNone(run.lumber)
        self.assertIsNone(run.competition)

    def test_mining_run_complete_not_unique_ores_combinations_raises_error(self):
        run = self.make_incomplete_run()
        test_ores = [
            MinedOre(OreType.COPPER, OreQuality.BRONZE, 0),
            MinedOre(OreType.COPPER, OreQuality.SILVER, 10),
            MinedOre(OreType.COPPER, OreQuality.SILVER, 100),
            MinedOre(OreType.TIN, OreQuality.BRONZE, 5),
            MinedOre(OreType.TIN, OreQuality.BRONZE, 15),
            MinedOre(OreType.TIN, OreQuality.GOLD, 155),
            MinedOre(OreType.SILVER, OreQuality.GOLD, 7),
            MinedOre(OreType.SILVER, OreQuality.SILVER, 39),
            MinedOre(OreType.SILVER, OreQuality.GOLD, 26),
        ]

        with self.assertRaises(MiningRunError):
            run.complete(
                test_ores,
                lumber=25,
                competition=Competition.MEDIUM,
                comment="Test comment",
            )

        self.assertNotEqual(run.status, Status.COMPLETED)
        self.assertIsNone(run.ores)
        self.assertIsNone(run.lumber)
        self.assertIsNone(run.competition)

    def test_mining_run_complete_twice_raises_error(self):
        run = self.make_incomplete_run()
        run.complete(
            self.test_ores,
            lumber=24,
            competition=Competition.LOW,
            comment="Test comment",
        )

        test_ores2 = [
            MinedOre(OreType.COPPER, OreQuality.BRONZE, 5),
            MinedOre(OreType.COPPER, OreQuality.SILVER, 20),
            MinedOre(OreType.COPPER, OreQuality.GOLD, 133),
            MinedOre(OreType.TIN, OreQuality.BRONZE, 9),
            MinedOre(OreType.TIN, OreQuality.SILVER, 15),
            MinedOre(OreType.TIN, OreQuality.GOLD, 133),
            MinedOre(OreType.SILVER, OreQuality.BRONZE, 0),
            MinedOre(OreType.SILVER, OreQuality.SILVER, 9),
            MinedOre(OreType.SILVER, OreQuality.GOLD, 22),
        ]

        with self.assertRaises(MiningRunError):
            run.complete(
                test_ores2,
                lumber=38,
                competition=Competition.HIGH,
                comment="Test comment",
            )

        self.assertEqual(run.ores, tuple(self.test_ores))
        self.assertEqual(run.lumber, 24)
        self.assertEqual(run.competition, Competition.LOW)
        self.assertEqual(run.comment, "Test comment")
        self.assertEqual(run.status, Status.COMPLETED)
