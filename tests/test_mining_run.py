import unittest
import datetime as dt

from wow_oreacle.mining_run import MiningRun, MiningRunError, Status


class TestMiningRun(unittest.TestCase):
    def setUp(self) -> None:
        self.mr_start = MiningRun(
            unique_id="MR-0001",
            zone="Eversong Woods",
            route="Mining Only",
            start_time=dt.datetime(2026, 9, 22, 22, 45),
        )

        self.mr_incomplete = MiningRun(
            unique_id="MR-0001",
            zone="Eversong Woods",
            route="Mining Only",
            start_time=dt.datetime(2026, 9, 22, 22, 45),
            end_time=dt.datetime(2026, 9, 22, 23, 36),
        )
        self.mr_incomplete._status = Status.INCOMPLETE

    def test_mining_run_start_initialization(self):
        self.assertEqual(self.mr_start.unique_id, "MR-0001")
        self.assertEqual(self.mr_start.zone, "Eversong Woods")
        self.assertEqual(self.mr_start.route, "Mining Only")
        self.assertEqual(self.mr_start.start_time, dt.datetime(2026, 9, 22, 22, 45))
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
