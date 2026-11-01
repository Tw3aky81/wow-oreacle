from datetime import datetime, timezone
from unittest.mock import Mock, patch

from click.testing import CliRunner

from wow_oreacle.cli import cli
from wow_oreacle.mined_ore import MinedOre, OreType, OreQuality
from wow_oreacle.mining_run import Competition, MiningRun


def test_mininrun_start():
    app = Mock()
    commit = Mock()

    app.start_mining_run.return_value.start_time = datetime(
        2026, 10, 31, 9, 0, tzinfo=timezone.utc
    )

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["miningrun", "start", "--zone", "Eversong Woods", "--route", "Mining Only"],
        obj={"app": app, "commit": commit},
    )

    assert result.exit_code == 0
    app.start_mining_run.assert_called_once_with("Eversong Woods", "Mining Only")
    assert "Mining run started in" in result.output
    assert "Started at: 2026-10-31 10:00:00 CET" in result.output


def test_miningrun_start_interactive():
    app = Mock()
    commit = Mock()

    app.start_mining_run.return_value.start_time = datetime(
        2026, 10, 31, 9, 0, tzinfo=timezone.utc
    )

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["miningrun", "start"],
        obj={"app": app, "commit": commit},
        input="Eversong Woods\nMining Only\n",
    )

    assert result.exit_code == 0
    app.start_mining_run.assert_called_once_with("Eversong Woods", "Mining Only")
    assert "Mining run started in" in result.output
    assert "Started at: 2026-10-31 10:00:00 CET" in result.output


def test_miningrun_stop_interrupted():
    app = Mock()
    commit = Mock()

    app.stop_mining_run.return_value.end_time = datetime(
        2026, 10, 31, 10, 0, tzinfo=timezone.utc
    )

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["miningrun", "stop"],
        obj={"app": app, "commit": commit},
        input="120\n",
    )

    assert result.exit_code != 0
    assert "Aborted!" in result.output

    app.stop_mining_run.assert_called_once()
    commit.assert_called_once()
    app.complete_mining_run.assert_not_called()


def test_miningrun_stop():
    app = Mock()
    commit = Mock()

    app.stop_mining_run.return_value.unique_id = 1
    app.stop_mining_run.return_value.end_time = datetime(
        2026, 10, 31, 10, 0, tzinfo=timezone.utc
    )

    completed_run = app.complete_mining_run.return_value
    completed_run.unique_id = 1
    completed_run.duration_in_hours.return_value = 1.00
    completed_run.total_ore.return_value = 387
    completed_run.total_lumber.return_value = 24
    completed_run.ore_per_hour.return_value = 387.00
    completed_run.lumber_per_hour.return_value = 24.00

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["miningrun", "stop"],
        obj={"app": app, "commit": commit},
        input=(
            "120\n"  # Copper Bronze
            "80\n"  # Copper Silver
            "40\n"  # Copper Gold
            "60\n"  # Tin Bronze
            "30\n"  # Tin Silver
            "10\n"  # Tin Gold
            "15\n"  # Silver Bronze
            "5\n"  # Silver Silver
            "2\n"  # Silver Gold
            "25\n"  # Lumber
            "L\n"  # Competition: Low
            "Good run\n"  # Comment
        ),
    )

    assert result.exit_code == 0
    assert commit.call_count == 1
    app.complete_mining_run.assert_called_once_with(
        1,
        [
            MinedOre(OreType.COPPER, OreQuality.BRONZE, 120),
            MinedOre(OreType.COPPER, OreQuality.SILVER, 80),
            MinedOre(OreType.COPPER, OreQuality.GOLD, 40),
            MinedOre(OreType.TIN, OreQuality.BRONZE, 60),
            MinedOre(OreType.TIN, OreQuality.SILVER, 30),
            MinedOre(OreType.TIN, OreQuality.GOLD, 10),
            MinedOre(OreType.SILVER, OreQuality.BRONZE, 15),
            MinedOre(OreType.SILVER, OreQuality.SILVER, 5),
            MinedOre(OreType.SILVER, OreQuality.GOLD, 2),
        ],
        25,
        Competition.LOW,
        "Good run",
    )
    assert "Mining run stopped." in result.output
    assert "Stopped at: 2026-10-31 11:00:00 CET" in result.output
    assert "Mining run with ID 1 completed." in result.output
    assert "Duration: 1.00 hours" in result.output
    assert "Total ores: 387" in result.output
    assert "Ores per hour: 387.00" in result.output
    assert "Total lumber: 24" in result.output
    assert "Lumber per hour: 24.00" in result.output


def test_miningrun_complete_selection():
    app = Mock()
    commit = Mock()

    run1 = MiningRun.start_new("Eversong Woods", "Mining Only")
    run1.unique_id = 42
    run1.stop()

    run2 = MiningRun.start_new("Ghostlands", "Mining Only")
    run2.unique_id = 87
    run2.stop()

    end_time1 = run1.end_time
    end_time2 = run2.end_time

    assert end_time1 is not None
    assert end_time2 is not None

    app.get_incomplete_mining_runs.return_value = [run1, run2]

    completed_run = app.complete_mining_run.return_value
    completed_run.duration_in_hours.return_value = 1.50
    completed_run.total_ore.return_value = 245
    completed_run.total_lumber.return_value = 24
    completed_run.ore_per_hour.return_value = 163.33
    completed_run.lumber_per_hour.return_value = 16.00

    runner = CliRunner()
    with patch("wow_oreacle.cli.prompt_mining_results") as prompt_results:
        prompt_results.return_value = ([], 0, Competition.NONE, "")

        result = runner.invoke(
            cli,
            ["miningrun", "complete"],
            obj={"app": app, "commit": commit},
            input=(
                "2\n"  # User chose run 2
            ),
        )

    assert result.exit_code == 0, repr(result.exception)
    app.get_incomplete_mining_runs.assert_called_once()
    assert "Incomplete mining runs:" in result.output
    assert (
        f"1. {end_time1.astimezone():%Y-%m-%d %H:%M}  Eversong Woods - Mining Only"
        in result.output
    )
    assert (
        f"2. {end_time2.astimezone():%Y-%m-%d %H:%M}  Ghostlands - Mining Only"
        in result.output
    )
    assert "Select mining run [1]:" in result.output
    app.complete_mining_run.assert_called_once_with(
        87,
        [],
        0,
        Competition.NONE,
        "",
    )


def test_miningrun_complete():
    app = Mock()
    commit = Mock()

    run1 = MiningRun.start_new("Eversong Woods", "Mining Only")
    run1.unique_id = 42
    run1.stop()

    run2 = MiningRun.start_new("Ghostlands", "Mining Only")
    run2.unique_id = 87
    run2.stop()

    end_time1 = run1.end_time
    end_time2 = run2.end_time

    assert end_time1 is not None
    assert end_time2 is not None

    app.get_incomplete_mining_runs.return_value = [run1, run2]

    completed_run = app.complete_mining_run.return_value
    completed_run.unique_id = 87
    completed_run.duration_in_hours.return_value = 1.50
    completed_run.total_ore.return_value = 362
    completed_run.total_lumber.return_value = 25
    completed_run.ore_per_hour.return_value = 241.33
    completed_run.lumber_per_hour.return_value = 16.66

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["miningrun", "complete"],
        obj={"app": app, "commit": commit},
        input=(
            "2\n"  # User chose run 2
            "120\n"  # Copper Bronze
            "80\n"  # Copper Silver
            "40\n"  # Copper Gold
            "60\n"  # Tin Bronze
            "30\n"  # Tin Silver
            "10\n"  # Tin Gold
            "15\n"  # Silver Bronze
            "5\n"  # Silver Silver
            "2\n"  # Silver Gold
            "25\n"  # Lumber
            "L\n"  # Competition: Low
            "Good run\n"  # Comment
        ),
    )

    assert result.exit_code == 0, repr(result.exception)
    app.complete_mining_run.assert_called_once_with(
        87,
        [
            MinedOre(OreType.COPPER, OreQuality.BRONZE, 120),
            MinedOre(OreType.COPPER, OreQuality.SILVER, 80),
            MinedOre(OreType.COPPER, OreQuality.GOLD, 40),
            MinedOre(OreType.TIN, OreQuality.BRONZE, 60),
            MinedOre(OreType.TIN, OreQuality.SILVER, 30),
            MinedOre(OreType.TIN, OreQuality.GOLD, 10),
            MinedOre(OreType.SILVER, OreQuality.BRONZE, 15),
            MinedOre(OreType.SILVER, OreQuality.SILVER, 5),
            MinedOre(OreType.SILVER, OreQuality.GOLD, 2),
        ],
        25,
        Competition.LOW,
        "Good run",
    )
    assert "Mining run with ID 87 completed." in result.output
    assert "Duration: 1.50 hours" in result.output
    assert "Total ores: 362" in result.output
    assert "Ores per hour: 241.33" in result.output
    assert "Total lumber: 25" in result.output
    assert "Lumber per hour: 16.66" in result.output


def test_get_stats():
    app = Mock()
    app.get_stats.return_value = {
        "completed_runs": 2,
        "total_hours": 3.0,
        "total_ores": 170,
        "ores_per_hour": 170 / 3,
        "total_lumber": 140,
        "lumber_per_hour": 140 / 3,
    }
    commit = Mock()
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["stats"],
        obj={"app": app, "commit": commit},
    )

    assert result.exit_code == 0, repr(result.exception)
    app.get_stats.assert_called_once()
