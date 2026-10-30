from unittest.mock import Mock
from click.testing import CliRunner
from wow_oreacle.cli import cli


def test_mininrun_start():
    app = Mock()
    runner = CliRunner()

    result = runner.invoke(
        cli,
        ["miningrun", "start", "--zone", "Eversong Woods", "--route", "Mining Only"],
        obj=app,
    )

    assert result.exit_code == 0
    app.start_mining_run.assert_called_once_with("Eversong Woods", "Mining Only")
    assert "Mining run started in" in result.output
    assert "Started at:" in result.output


def test_miningrun_start_interactive():
    app = Mock()
    runner = CliRunner()

    result = runner.invoke(
        cli,
        ["miningrun", "start"],
        input="Eversong Woods\nMining Only\n",
        obj=app,
    )

    assert result.exit_code == 0
    app.start_mining_run.assert_called_once_with("Eversong Woods", "Mining Only")
    assert "Mining run started in" in result.output
    assert "Started at:" in result.output
