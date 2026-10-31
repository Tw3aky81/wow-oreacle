from unittest.mock import Mock

from click.testing import CliRunner

from wow_oreacle.cli import cli


def test_mininrun_start():
    app = Mock()
    commit = Mock()

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["miningrun", "start", "--zone", "Eversong Woods", "--route", "Mining Only"],
        obj={"app": app, "commit": commit},
    )

    assert result.exit_code == 0
    app.start_mining_run.assert_called_once_with("Eversong Woods", "Mining Only")
    assert "Mining run started in" in result.output
    assert "Started at:" in result.output


def test_miningrun_start_interactive():
    app = Mock()
    commit = Mock()

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
    assert "Started at:" in result.output


def test_miningrun_stop_interrupted():
    app = Mock()
    commit = Mock()

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
