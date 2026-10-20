import unittest
import datetime as dt

from wow_oreacle.mining_run import MiningRun, MiningRunError, Status


class TestMiningRun(unittest.TestCase):
    def test_mining_run_start_initialization(self):
        mr = MiningRun(
            unique_id="MR-0001",
            zone="Eversong Woods",
            route="Mining Only",
            start_time=dt.datetime(2026, 9, 22, 22, 45),
        )
        self.assertIsInstance(mr.unique_id, str)
        self.assertEqual(mr.unique_id, "MR-0001")
        self.assertIsInstance(mr.zone, str)
        self.assertEqual(mr.zone, "Eversong Woods")
        self.assertIsInstance(mr.route, str)
        self.assertEqual(mr.route, "Mining Only")
        self.assertIsInstance(mr.start_time, dt.datetime)
        self.assertEqual(mr.start_time.year, 2026)
        self.assertEqual(mr.start_time.month, 9)
        self.assertEqual(mr.start_time.day, 22)
        self.assertEqual(mr.start_time.hour, 22)
        self.assertEqual(mr.start_time.minute, 45)
        self.assertEqual(mr.status, Status.ACTIVE)

        self.assertIsNone(mr.end_time)
        self.assertIsNone(mr.ores)
        self.assertIsNone(mr.lumber)

    def test_mining_run_status_is_read_only(self):
        mr = MiningRun(
            unique_id="MR-0001",
            zone="Eversong Woods",
            route="Mining Only",
            start_time=dt.datetime(2026, 9, 22, 22, 45),
        )

        with self.assertRaises(AttributeError):
            mr.status = Status.COMPLETED

    def test_mining_run_active_ore_per_hour_raises_error(self):
        mr = MiningRun(
            unique_id="MR-0001",
            zone="Eversong Woods",
            route="Mining Only",
            start_time=dt.datetime(2026, 9, 22, 22, 45),
        )
        with self.assertRaises(MiningRunError):
            mr.ore_per_hour()

    def test_mining_run_active_duration_in_hours_raises_error(self):
        mr = MiningRun(
            unique_id="MR-0001",
            zone="Eversong Woods",
            route="Mining Only",
            start_time=dt.datetime(2026, 9, 22, 22, 45),
        )
        with self.assertRaises(MiningRunError):
            mr.duration_in_hours()

    def test_mining_run_active_total_ore_raises_error(self):
        mr = MiningRun(
            unique_id="MR-0001",
            zone="Eversong Woods",
            route="Mining Only",
            start_time=dt.datetime(2026, 9, 22, 22, 45),
        )
        with self.assertRaises(MiningRunError):
            mr.total_ore()
