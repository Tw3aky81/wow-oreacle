# wow-oreacle

wow-oreacle is a work-in-progress Python project for tracking mining runs in World of Warcraft. The goal is to record runs and compare their yields over time; today, the repository contains the beginnings of the domain model, not a usable command-line application.

## Current state

- `MinedOre` represents an ore type, quality, and non-negative integer amount. It is immutable.
- `MiningRun` holds a run's ID, zone, route, start and optional end time, materials, optional competition (`NONE`, `LOW`, `MEDIUM`, or `HIGH`), and status (`ACTIVE`, `INCOMPLETE`, or `COMPLETED`). Its status starts as `ACTIVE` and is read-only through the public `status` property; there is no public lifecycle transition method yet.
- `MiningRun` calculates duration in hours when an end time exists, and total ore and ore per hour when its status is `COMPLETED`. It does not yet validate all run invariants: for example, a completed run with a zero-length duration will raise `ZeroDivisionError` when calculating ore per hour.
- There is no CLI, database, route configuration, or persistence yet. Runs must currently be created in Python code.

## Requirements and setup

Python 3.15 or newer is required. The project has no runtime dependencies. From the repository root, install it in a virtual environment using either `uv` or `pip`:

```sh
uv sync
# Or, in an activated virtual environment:
python -m pip install -e .
```

## Example

```python
from datetime import datetime, timedelta

from wow_oreacle.mined_ore import MinedOre, OreQuality, OreType
from wow_oreacle.mining_run import MiningRun

start = datetime.now()
run = MiningRun(
    unique_id="run-1",
    zone="Example zone",
    route="Example route",
    start_time=start,
    end_time=start + timedelta(hours=1),
    ores=[MinedOre(OreType.COPPER, OreQuality.BRONZE, 25)],
)

print(run.status.name)          # ACTIVE
print(run.duration_in_hours())  # 1.0
print(run.ores[0].amount)       # 25
```

`MinedOre` rejects invalid ore types, qualities, non-integer amounts, and negative amounts. `MiningRun.total_ore()` and `MiningRun.ore_per_hour()` raise `MiningRunError` unless the status is `COMPLETED`; `duration_in_hours()` raises it if there is no end time. The example sets an end time but the run remains `ACTIVE` because ending and completing runs are not implemented yet.

## Tests

From the repository root:

```sh
./test.sh
# Equivalent: uv run python -m unittest discover -s tests -v
```

The existing tests cover `MinedOre` and basic `MiningRun` initialization, status, duration, and error cases. Run workflows and storage are not yet implemented.

## Planned direction

The [design document](oreacle_design.md) describes the proposed v0.1 mining-run tracker: start and stop runs from a CLI, enter materials, save runs in SQLite, and inspect and compare completed runs. Prospecting, jewelcrafting, and market prices are longer-term ideas. The design describes intended behavior rather than features already available.
