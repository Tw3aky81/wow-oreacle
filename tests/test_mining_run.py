import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from wow_oreacle.mined_ore import MinedOre, OreQuality, OreType
from wow_oreacle.mining_run import Competition, MiningRun, MiningRunError, Status


class TestMiningRun(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_start_time = datetime(2026, 10, 20, 12, 0, tzinfo=timezone.utc)
        self.mock_end_time = datetime(2026, 10, 20, 13, 30, tzinfo=timezone.utc)

        self.mr_start = MiningRun(
            unique_id=1,
            zone="Eversong Woods",
            route="Mining Only",
            start_time=datetime(2026, 9, 22, 22, 45, tzinfo=timezone.utc),
        )

        self.mr_incomplete = MiningRun(
            unique_id=127,
            zone="Eversong Woods",
            route="Mining Only",
            start_time=datetime(2026, 9, 22, 22, 45, tzinfo=timezone.utc),
            end_time=datetime(2026, 9, 22, 23, 36, tzinfo=timezone.utc),
        )
        self.mr_incomplete._status = Status.INCOMPLETE

        test_ores = [
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
        self.mr_complete = MiningRun(
            unique_id=2938,
            zone="Eversong Woods",
            route="Mining Only",
            start_time=datetime(2026, 9, 22, 22, 45, tzinfo=timezone.utc),
            end_time=datetime(2026, 9, 22, 23, 36, tzinfo=timezone.utc),
            ores=test_ores,
            lumber=17,
            competition=Competition.MEDIUM,
            comment="Optional example comment",
        )
        self.mr_complete._status = Status.COMPLETED

    def test_mining_run_start_initialization(self):
        self.assertEqual(self.mr_start.unique_id, 1)
        self.assertEqual(self.mr_start.zone, "Eversong Woods")
        self.assertEqual(self.mr_start.route, "Mining Only")
        self.assertEqual(
            self.mr_start.start_time,
            datetime(2026, 9, 22, 22, 45, tzinfo=timezone.utc),
        )
        self.assertEqual(self.mr_start.status, Status.ACTIVE)

        self.assertIsNone(self.mr_start.end_time)
        self.assertIsNone(self.mr_start.ores)
        self.assertIsNone(self.mr_start.lumber)

    def test_mining_run_status_is_read_only(self):
        with self.assertRaises(AttributeError):
            self.mr_start.status = Status.COMPLETED

    def test_mining_run_active_duration_in_hours_raises_error(self):
        with self.assertRaises(MiningRunError):
            self.mr_start.duration_in_hours()

    def test_mining_run_active_ore_per_hour_raises_error(self):
        with self.assertRaises(MiningRunError):
            self.mr_start.ore_per_hour()

    def test_mining_run_active_total_ore_raises_error(self):
        with self.assertRaises(MiningRunError):
            self.mr_start.total_ore()

    def test_mining_run_incomplete_duration_in_hours(self):
        self.assertEqual(self.mr_incomplete.duration_in_hours(), 0.85)

    def test_mining_run_incomplete_ore_per_hour_raises_error(self):
        with self.assertRaises(MiningRunError):
            self.mr_incomplete.ore_per_hour()

    def test_mining_run_incomplete_total_ore_raises_error(self):
        with self.assertRaises(MiningRunError):
            self.mr_incomplete.total_ore()

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
