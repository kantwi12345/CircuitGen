# CircuitGen Project State

## Repository

https://github.com/kantwi12345/CircuitGen

## Project Goal

CircuitGen is an HFSS antenna automation platform built with Python,
FastAPI, and PyWin32. The system automatically generates antenna
geometries in Ansys Electronics Desktop (HFSS) through COM automation and
exposes the functionality through REST APIs, a CLI, and a web UI.

Geometry-only mode: excitation, analysis setup and frequency sweep are
configured manually in HFSS after geometry generation.

---

# Completed Work

## Infrastructure

Completed:

- FastAPI backend
- Swagger documentation
- HFSS COM connection
- HFSS project creation
- HFSS design creation
- HFSS design parameters (set, derive, validate, save, build)
- HFSS Local Variables (GUI automation)
- CLI + Web UI

Main files:

- backend/app.py
- tools/hfss_com.py
- tools/patch_builder.py
- tools/antenna_calcs.py
- tools/antenna_library.py
- tools/design_params.py
- tools/hfss_vars.py
- tools/hfss_sim.py
- tools/hfss_launch.py
- tools/hfss_project.py
- tools/interface.py

---

## Antenna Generators

### Design parameters (set before building)

`tools/design_params.py` - the design is specified, derived, validated and
saved **before** any HFSS model is built.

Set: name, antenna type, frequency, substrate (+ er / loss tangent /
thickness), feed type, and optional manual overrides (patch W/L, radiator
radius).

Derived: patch size, 50 ohm feed width (Hammerstad), feed length, board
size, radiation box, lambda0.

Endpoints:

- `POST /design/params` - set + derive + validate + save a parameter set
- `GET  /design/params` - list saved sets
- `GET  /design/params/{name}` - load one set
- `POST /design/build` - build the HFSS model from a saved set
- `POST /hfss/build` - accepts a saved `design` name, or derives a
  parameter set from the request and builds from it (the parameter set
  comes back with the result)

CLI:

```
python tools/interface.py design-params --name patch_2p4ghz_fr4 --frequency-ghz 2.4 --substrate FR4
python tools/interface.py list-designs
python tools/interface.py build-antenna --design patch_2p4ghz_fr4
```

Web UI: panel "1. Design Parameters (set before building)" -> derive and
save, then "2. Build Antenna in HFSS" (inline or from a saved set).

Saved sets live in `projects/designs/*.json`.

### HFSS design variables (Local Variables)

`tools/hfss_vars.py` writes the design parameters into the HFSS design as
**local variables** - they show up exactly where you pointed:

```
Properties: <project> - <design>  ->  Local Variables tab
```

| Antenna | Variables written |
|---|---|
| Patch | 20: f0, er, h, patch_w/l/x/y, feed_w/l/x, board_x/y, gnd_ext, port_x, air_x/y/z, air_sx/sy/sz |
| Monopole | 13: f0, rad_l/r/z, gnd_half, port_x/w, air_* |
| Dipole | 12: f0, dip_l/r, gap_l/r, port_x, air_* |

Notes:

- HFSS has no working COM call for this (`SetVariableValue` and
  `ChangeProperty` on `LocalVariableTab` are both rejected), so the
  Properties dialog is driven through the GUI (right-click the design ->
  "Design Properties..." -> Add... -> Add Property).
- The **Name** field takes the bare name (`f0`, not `$f0`) - HFSS adds
  the `$` itself and rejects a typed `$` with
  "must begin with a letter or an underscore".
- The GUI automation can take the calling process down with an access
  violation, so it runs in an **isolated child process**
  (`set_design_variables_isolated`).
- HFSS 2022 R1 **crashes** when a geometry field is driven by a variable
  expression (`$feed_l`), so the geometry is created with literal values
  and the variables are attached to the finished design.

### Parametric geometry (frequency-driven)

All HFSS generators are now driven by the operating frequency instead of
hard-coded dimensions:

| Antenna | Rule | 2.4 GHz value (unchanged from the validated model) |
|---|---|---|
| Patch | W/L from `patch_dimensions`, feed width from 50 ohm microstrip synthesis (Hammerstad), feed length = lambda0/8, board/air box scale with lambda0 | feed 3.0 x 16.0 mm |
| Monopole | radiator = lambda0/4, ground plane and radiation box scale with lambda0 | 31.25 mm |
| Dipole | radiator = lambda0/2, radiation box scales with lambda0 | 62.5 mm |

Modules:

- `tools/antenna_calcs.py` - `patch_layout`, `monopole_layout`,
  `dipole_layout`, `microstrip_width_50ohm`, `e24_round`
- `tools/patch_builder.py` - parametric patch generator (substrate material
  auto-selected: FR4_epoxy / rogers5880 / rogers4350b)
- `validate_antennas.py` - builds each antenna in HFSS at 0.9 / 1.8 / 2.4 /
  3.6 / 5.2 / 10 GHz and verifies the geometry HFSS actually created
  against the intended layout (positions, sizes, connectivity, clearance)

Validation result: **all antennas valid at all tested frequencies**.

---

## Patch Antenna

Status: Working

Implemented:

- Substrate
- Ground plane
- Patch
- Feed line
- Port sheet
- Air box
- Radiation boundary

Notes:

- Geometry generation working
- Simulation setup partially implemented
- Port geometry refined manually in HFSS

---

## Monopole Antenna

Status: Geometry Working

Implemented:

- Ground plane
- Monopole radiator
- Feed geometry
- Port sheet
- Air box
- Radiation boundary

Notes:

- Manual port assignment currently preferred

---

## Dipole Antenna

Status: Geometry Working

Implemented:

- Cylindrical dipole
- Feed gap
- Embedded port sheet
- Air region

Notes:

- Feed-gap modeling improved several times
- Port sheet embedded inside feed region

---

## Yagi-Uda Prototype

Status: Prototype

Implemented:

- Reflector
- Driven element
- Director 1
- Director 2
- Director 3
- Feed gap
- Port sheet
- Boom
- Feed cone
- Air box
- Radiation boundary

Notes:

- Dimensions are provisional
- Based on engineering assumptions
- Needs verification against reference HFSS tutorial

API Endpoint:

/hfss/build_yagi_prototype

---

# API Endpoints

Implemented:

GET  /health

GET  /tools

POST /design

GET  /hfss/new_project

POST /hfss/create_antenna

POST /hfss/build_patch

POST /hfss/build_monopole

POST /hfss/build_dipole

POST /hfss/build_yagi_prototype

POST /hfss/build

POST /design/params

GET  /design/params

GET  /design/params/{name}

POST /design/build

---

# Updates (HFSS-only focus)

- HFSS generators kept geometry-only (no excitation/setup/sweep automation).
- All ADS/circuit-related work removed; focus is HFSS antenna automation.
- Antenna types: patch, monopole, dipole, yagi.

# Current Challenges

1. Lumped-port automation (HFSS) - parked, manual in HFSS later
2. Reliable HFSS excitation creation - parked, manual later
3. Automatic solver setup generation - parked, manual later
4. Frequency sweep generation - parked, manual later
5. HFSS result extraction - parked, manual later

---

# Next Priorities

## Priority 1

HFSS Antenna Geometry

Goals:

- Parametric Yagi (element lengths/spacing from lambda0)
- Additional antenna types (loop, bow-tie, helical, horn, arrays)

## Priority 2

Gain / Radiation Extraction

Goals:

- Peak gain
- Radiation efficiency
- Directivity

## Priority 3

Simulation Automation

Goals:

- Create Setup1 automatically
- Create sweeps automatically
- Launch analysis automatically

## Priority 4

Optimization Engine

Goals:

- Parameter sweeps
- Geometry tuning
- AI-assisted optimization

---

# Future Antennas

Planned:

- Loop
- Bow-Tie
- Helical
- Horn
- Patch Arrays
- Log-Periodic
- Spiral

Current Milestone:

v0.4.0 (HFSS-only)

Major Features Completed:

- HFSS COM Integration
- FastAPI Backend
- Patch Generator (parametric, frequency-driven)
- Monopole Generator (parametric, frequency-driven)
- Dipole Generator (parametric, frequency-driven)
- Yagi Prototype Generator
- Design Parameters (HFSS) - set, derive, validate, save, build
- HFSS Local Variables (Design Properties -> Local Variables)
- Web Build Interface + CLI + REST API
- Comprehensive README documentation

---

# Handoff Instructions

If another AI continues this project:

1. Read README.md
2. Read PROJECT_STATE.md
3. Review backend/app.py
4. Review tools/hfss_com.py

Then continue with:

- Parametric Yagi (element lengths/spacing from lambda0)
- Additional antenna types
- S11 / gain extraction
- Optimization engine

The Yagi dimensions are currently provisional and should be validated against the original HFSS tutorial before production use.