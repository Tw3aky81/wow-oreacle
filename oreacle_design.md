# Oreacle — Design Document

> **Repository:** `wow-oreacle`
>
> **Application:** Oreacle
>
> **Status:** Working document — design before implementation
>
> **Last updated:** October 19, 2026

## 1. Purpose and guiding principles

Oreacle is a local **Python command-line application** for recording and analyzing activities in **World of Warcraft**, ultimately covering mining, prospecting, and jewelcrafting.

The project will eventually replace an existing spreadsheet, but it does not have to copy the spreadsheet literally. The spreadsheet serves as a **functional reference**, not a mandatory data model.

### Primary goal: learning to design and build

Oreacle is primarily a **personal learning project**, with a target budget of **20–40 hours** for a finished first version. The project should help me independently move from requirements to a working application, outside the structure of tutorials.

Special attention goes to:

- Software architecture and assigning responsibilities.
- Python data structures, classes/dataclasses, and domain modeling.
- Persistence, validation, error handling, and testability.
- Small, deliberate design decisions and maintainable code.
- Learning to refactor for concrete reasons, without overengineering.

**Working agreement:** I design and implement the application. The mentor asks questions, provides hints, discusses alternatives, and reviews code; complete solutions are given only on request.

## 2. Current workflow and problem

### Mining

1. Choose a zone and route from the WoW **Routes** addon.
2. Record the start time.
3. Mine one lap or repeat the same route for a period of time.
4. Record the end time.
5. Check the inventory and count the materials collected.
6. Record the run in the spreadsheet: date, start time, zone, route (currently sometimes in notes), duration, ore by type and quality, lumber, competition, and any notes.
7. Review calculations such as total ore, ore per hour, and lumber per hour.

**Pain point:** a lot of manual administration, especially timestamps, material quantities, and recordkeeping. Oreacle should simplify recording and make it possible to compare runs.

### Other spreadsheet workflows

- **Prospecting:** ores used and their quantities, output, costs, and returns.
- **Jewelcrafting:** reagent costs, crafted items, sale prices, Auction House cut, net profit, and ROI.

These workflows belong to the long-term vision, **not** the first MVP.

A manually maintained **Market Prices** tab is not a desired part of the design: the maintenance effort outweighs its value. Any AH price integration should be evaluated separately later.

The spreadsheet dashboard is a non-functional concept and is out of scope.

## 3. Functional goal for v0.1

**Oreacle v0.1 is a mining-run tracker.** The application should be able to start and stop mining sessions, record yields, save them durably, and provide insight into efficiency.

### MVP — intended functionality

- Start a mining session via the CLI, choosing a **zone** and **route**.
- Stop an active session; Oreacle records the start and end times.
- Enter collected materials afterward.
- Save a run locally and durably in SQLite.
- Browse previous runs.
- Calculate total ore, ore per hour, and optionally lumber per hour.
- Compare yields across runs and routes; the exact initial reports still need to be scoped.
- Handle invalid input and invalid state transitions.
- Verify the core logic with automated tests.

### Outside v0.1 / to investigate later

- Prospecting and jewelcrafting functionality.
- Auction House prices or price history.
- Dashboard or graphical interface.
- REST API.
- CSV import/export.
- Detailed reports by weekday and time slot.
- CLI management of zones and routes.
- Automatic import from the Routes addon.
- Support for materials from future WoW expansions.

**Still to decide for v0.1:** whether editing/correcting completed runs afterward belongs in the minimum release. It is a desired feature.

## 4. Desired analyses

Over time, the data should be able to answer:

1. How much ore (and lumber) did a run yield per hour?
2. What is the average yield of a given route?
3. Which route performs best within a zone?
4. Which zone has the highest average yield?
5. Which days and times yield the best results on average?

**Design principle:** store the source data (including full start and end times) so analyses can be added later, but do not implement every analysis in v0.1.

**Open statistical decision:** the arithmetic mean of individual `ore/hour` values is not the same as `sum(ore) / sum(duration)`; for route and zone comparisons, a metric and its rationale still need to be chosen. Competition may also affect interpretation.

## 5. Initial architecture

The chosen **direction** is a simple dependency chain:

```text
CLI  →  Mining (domain logic)  →  Persistence  →  SQLite
```

### CLI

- Parse commands.
- Display selection menus, ask questions, and collect input.
- Convert terminal input into usable Python values.
- Call mining functionality.
- Display results and understandable error messages.
- Preferably contain **no mining business rules**.

### Mining module

- Model `MiningRun` and its associated rules.
- Check domain validation, such as non-negative quantities and valid time relationships.
- Manage the lifecycle of a mining run.
- Determine whether a new run may start.
- Contain calculations and, eventually, mining analyses.
- Retrieve information through the persistence layer when needed, without writing SQL itself.
- Preferably know nothing about `input()` or `print()`.

### Persistence module

- Save and retrieve runs using Python's built-in `sqlite3`.
- For example, find the active run.
- Handle database operations and transactions.
- Does not need to determine the reason behind a domain rule.

**Important boundary:** the CLI may call Mining; Mining does not need to call the CLI. Avoid mutual imports and unnecessary abstraction layers. The exact file structure, functions, and any service classes are not yet fixed.

### Validation

- **Input validation (CLI):** can text be interpreted as an integer or date/time?
- **Domain validation (Mining):** is a value or state valid within a mining run?
- **Database integrity (Persistence/SQLite):** where useful, prevent storage from ending up in an inconsistent state.

An action may return a value or object, or use an exception for errors. This is **not yet decided**; a simple success boolean is not automatically the best API.

## 6. Domain model: `MiningRun`

A `MiningRun` represents one specific mining session, similar to a row in the current mining sheet, but with its own behavior and rules.

### Preliminary information categories

| Category | Data |
| --- | --- |
| Identity | Unique ID (format still to be decided) |
| Context | Zone, route, competition, optional note |
| Time | Start time, end time (initially unknown) |
| Mining yield | Copper, Tin, and Silver, each in Q1/Q2/Q3 |
| Other yield | Lumber; any other current materials still to be verified |
| Lifecycle | ACTIVE / INCOMPLETE / COMPLETED |

The exact attributes, types, defaults, representation of the nine ore quantities, and any nullable fields still need to be designed.

A Python **`@dataclass`** is tentatively preferred because the object primarily represents related data but can also contain methods. This is not yet a complete class definition.

### Calculated data

- `total_ore` is calculated from the relevant ore quantities.
- `ore_per_hour = total_ore / duration_in_hours`.
- `lumber_per_hour = lumber / duration_in_hours`.
- Duration follows from the start and end times.

**Decision:** in principle, store the original data and **calculate derived values when needed**. This prevents old calculated values from becoming inconsistent when calculation rules change.

Calculations are only valid when the required data exists and the duration is positive; behavior for an active/incomplete run still needs to be explicitly designed.

### Corrections

Ultimately, a user should be able to correct input errors in existing runs (for example, a miscounted quantity). The exact rules and timing within the MVP remain open.

## 7. Mining-run lifecycle

The provisionally agreed state model:

```text
ACTIVE  --stop + save end time-->  INCOMPLETE
INCOMPLETE  --complete and valid materials-->  COMPLETED
```

| Status | Meaning | Start time | End time | Materials | Included in statistics? |
| --- | --- | --- | --- | --- | --- |
| `ACTIVE` | Mining is in progress | Yes | No | Not yet recorded | No |
| `INCOMPLETE` | Stopped, input still needs to be finished | Yes | Yes | Missing or incomplete | No |
| `COMPLETED` | Run is finished and valid | Yes | Yes | Complete | Yes |

### Rules

- There may be **at most one ACTIVE run** at a time.
- Multiple INCOMPLETE runs are allowed and do not block a new run.
- Only COMPLETED runs count toward aggregations and comparisons.
- An INCOMPLETE run can be filled in later, preserving the **original end time**.
- A run is not automatically COMPLETED just because its end time is known.

An explicit persistent `status` attribute was chosen to represent these three states. The application must ensure **consistency between status and times**.

### Start workflow (conceptual)

1. The CLI receives `oreacle mining start`.
2. The user chooses a zone and route.
3. Mining asks Persistence whether an ACTIVE run already exists.
4. If there is an active run, starting another is rejected with a clear message.
5. Otherwise, the new ACTIVE run is saved with its start time.

### Stop workflow (agreed order)

1. Check whether an ACTIVE run exists.
2. Record the **end time** and set the status to INCOMPLETE.
3. **Save this durably immediately** before asking the user to enter material quantities.
4. Ask the user for the materials collected.
5. Validate the complete input.
6. Update the INCOMPLETE run and set its status to COMPLETED.
7. Save the data and status change together reliably.

Saving materials + changing status logically belongs in a single SQLite transaction: an error must not leave behind a partially updated COMPLETED run.

**Crash scenario:** if the program crashes after the end time has been saved but before all materials have been entered, the run remains INCOMPLETE and can be finished later. If the PC fails before `stop` is run, the actual end time is unknown; a future option for manual time correction may be needed.

## 8. Zones and routes

A zone can contain **multiple routes**. The route belongs in a run as a separate field, not only in notes.

### For v0.1

- The user chooses a zone and then a route through **numbered terminal menus**.
- The list of available zones and routes is initially **maintained manually in a JSON file**.
- JSON serves as a simple configuration/selection list; **SQLite** stores the history of mining runs.
- The exact JSON structure is not yet final.

Example of a possible configuration (not binding):

```json
{
  "Eversong Woods": ["Northern Loop", "Southern Loop"],
  "Zul'Aman": ["Eastern Route", "Western Route"]
}
```

### Later

- CLI commands for management, such as `oreacle zone add <name>` and `oreacle route remove <name>`; the command syntax is illustrative for now.
- Possibly import or synchronize route data from the WoW **Routes** addon and its SavedVariables. The exact file location and format still need investigation.
- Historical runs must remain understandable if a route is later renamed or removed from the current selection list.

## 9. Proposed development milestones

This is a **working hypothesis**, not a fixed architecture or deadline.

| Milestone | Goal | Scope |
| --- | --- | --- |
| **1. Domain model** | Design and test `MiningRun` | Dataclass/attributes, states, validation, calculations; no CLI/SQLite yet |
| **2. Persistence** | Save and retrieve runs durably | SQLite, finding the active run, transactions |
| **3. CLI & workflows** | Make start/stop and material entry usable | Commands, numeric zone/route selection from JSON, error messages |
| **4. Insights** | History and initial route comparison | List/overview, statistics for COMPLETED runs |
| **5. Completion** | Deliver v0.1 as a standalone project | Tests, README, refactoring, error scenarios |

**Indicative time budget (32 hours):** requirements/design 5h; CLI and domain logic 10h; persistence 6h; analysis/reporting 5h; tests/refactoring/documentation 6h. This is not a promise that every feature will fit within this budget: reduce scope when necessary.

### Immediate next step

First, independently design a **sketch of `MiningRun`**: class definition, attributes, type hints, and any defaults; **no methods, SQL, or CLI yet**. Then discuss the representation of materials and optional fields before implementation.

## 10. Open design questions / decision log

These questions are intentionally left open. Decide them when they become relevant.

- [ ] Exact attributes and type hints of `MiningRun`.
- [ ] Nine ore quantities as separate attributes or a grouped data structure?
- [ ] How is missing material data distinguished from a real quantity of `0`?
- [ ] Which competition values and any other materials are needed?
- [ ] How are start/end times stored and compared (time zone, datetime format)?
- [ ] How do calculations behave for ACTIVE and INCOMPLETE runs or a zero duration?
- [ ] What do domain errors and return values look like in practice?
- [ ] What is the minimum command set for v0.1?
- [ ] Which initial comparison metric for routes/zones: average of run rates or total ore / total duration?
- [ ] Which changes to COMPLETED runs are already allowed in v0.1?
- [ ] What happens after an error during stopping, and how does the user finish an old INCOMPLETE run?
- [ ] Which persistence constraints ensure valid statuses and at most one ACTIVE run?
- [ ] Which fields does SQLite store, and how does history remain stable when a route is renamed?
- [ ] Final JSON structure and location of the zone/route configuration.

## 11. Design principles and review questions

Use this document during implementation and code reviews. For important decisions, ask:

1. **Is this necessary for v0.1?** If not, can it wait?
2. **Is the responsibility clear?** Does it belong in CLI, Mining, or Persistence?
3. **Can I test the mining logic without a terminal or database?**
4. **Are we storing source data rather than unnecessary derived values?**
5. **What happens with invalid input, interrupted processes, and partially completed operations?**
6. **Do we really need this abstraction now, or does it make things unnecessarily complex?**
7. **Can I explain why I chose this solution and which alternative I rejected?**

> **Document discipline:** update this design when new insights lead to a better decision. For material changes, record **what** changed and **why**. The design is a tool for thinking, not an immutable contract.

## 12. Change log

| Date | Change |
| --- | --- |
| 2026-10-19 | Initial design document drafted based on the discovery and architecture discussion. |
