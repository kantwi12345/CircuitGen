# CircuitGen Project State

## Repository

https://github.com/kantwi12345/CircuitGen

## Project Goal

CircuitGen is an HFSS + ADS automation platform built with Python, FastAPI, and PyWin32.

The system automatically generates antenna geometries in HFSS through COM automation and exposes the functionality through REST APIs.

A parallel automation layer targets ADS for active/passive circuit builds.

---

# Completed Work

## Infrastructure

Completed:

- FastAPI backend
- Swagger documentation
- HFSS COM connection
- HFSS project creation
- HFSS design creation
- ADS launch/status/build command layer
- FastAPI command interface (`/ads/build`, `/hfss/build`)

Main files:

- backend/app.py
- tools/hfss_com.py
- tools/ads.py
- tools/ads_project.py

---

## Active Circuit Designs

### Class AB Audio Power Amplifier

Status: Design Complete (build-stage verified)

Design:

- Class: Class AB
- Output power: 50 W RMS
- Load: 8 ohm
- Supply: +/-35 V dual rail
- Closed-loop gain: 101 (40.09 dB)
- Design script: tools/... audio_amp_design.m (repo root)

Notes:

- ADS COM automation unavailable -> substituted MATLAB R2025b (build verified, exit 0)
- Fabrication/simulation -> ADS going forward

---

## ADS Build Flow (follows the ADS 2023 GUI process)

Per design, in this order:

1. **Workspace** (`File > New > Workspace` wizard values prepared):
   - Path `C:\ADS_Projects\<Design_Name>` (underscores, no spaces)
   - Local design library `<Design_Name>_lib`
   - Analog/RF libraries, layout units `mm`
   - `workspace_setup.md` lists every wizard field to enter
2. **Schematic** (`File > New > Schematic`):
   - Cell name without spaces (e.g. `lna`, `matching_network`)
   - Palette: Lumped-Components (R/C/L), Sources (V/I/E/G)
   - Build sheet lists every part, value, net and ground node
   - Ctrl+R rotate, Ctrl+W wires, Insert Ground, Ctrl+S save
3. **Simulation setup**: S-Parameter/DC/Transient, TermG ports, frequency sweep

Artifacts per design:

- `C:\ADS_Projects\<Design>\<Design>_lib\<cell>_build_sheet.md`
- `C:\ADS_Projects\<Design>\<Design>_lib\netlists\<cell>.net`
- `C:\ADS_Projects\<Design>\DESIGN_REPORT.md`
- Versioned copies in `projects\<Design_Name>\`

Designs available:

- Active: `Class AB Audio Power Amplifier`, `PA`, `LNA`
- Passive: `Impedance Matching Network`

Verification:

- L-match (50 ohm -> 36.5 ohm @ 2.4 GHz): Zin = 49.89 - 0.21j ohm, |S11| = 0.0024 (-52.6 dB)
- LNA (2.4 GHz): optimised + simulated -> Av = 16.11 dB, S11 = -20.20 dB,
  -3 dB BW = 82.3 MHz (2.336-2.418 GHz), NF estimate 1.34 dB (assumed F_min)

---

## ADS Automation Limits (verified experimentally)

| Route | Result |
|---|---|
| ADS COM automation (`Keysight.Ads.*` ProgIDs) | Not registered - no COM server in the registry |
| `ads.exe <workspace.ads>` | Ignored - ADS never touched the workspace |
| `ads.exe <workspace_dir>` | Ignored - same result |
| Windows file association for `.ads` / `.wrk` | Not registered |
| Authoring a schematic cell | `sch.oa` is binary OpenAccess - not authorable |

Verified by pointing `ads.exe` at the user's own known-good workspace
(`C:\Users\Hulede\RF_PA_wrk`): ADS did not modify it, so the CLI route is
unavailable in general, not just for generated workspaces.

Consequence: the workspace is generated on disk in the exact ADS 2023 format
(cloned file set from the reference workspace) and the user attaches it once
via **File > Open Workspace...**, then creates the schematic cell per the
documented ADS flow using the generated build sheet (or imports the netlist).

### ADS GUI automation (tools/ads_attach.py)

Because ADS exposes no CLI/COM path, the attach sequence is driven through
the ADS GUI with pywinauto (UIA backend):

1. Launch ADS (dismissing the "Product Selection" bundle dialog if shown)
2. `File > Open > Workspace...` -> type the workspace folder -> "Select Folder"
3. Toolbar **New Schematic** -> cell name -> Create

Verified: the workspace opens in ADS (tree shows the path, ADS rewrites
`de_sim.cfg` / `hpeesofsim.cfg` on load) and the cell is created on disk as
`<workspace>_lib/<cell>/schematic/sch.oa` - the same structure as the
reference `RF_PA_lib` cells.

Usage:

```
python tools/ads_attach.py --workspace C:\ADS_Projects\LNA_wrk --cell lna
```

or via the build flow / API: `open_in_ads=True`
(`POST /ads/build` body, `tools/interface.py build-circuit --open-ads`, or the
"Attach workspace & create schematic cell in ADS" checkbox in the web UI).

### AEL macro generation (tools/ads_ael.py)

ADS macros are AEL scripts (ADS records them as `*.mac` / `*.dem`). The
generator emits an AEL script that recreates the netlist as a schematic,
using the design-editor API found in the ADS AEL sources
(`de_create_new_schematic_view`, `de_iff_add_component`, `place_instance`,
`add_wire`, `named_connection`, `db_add_string_parm_to_instance`).

The macro is generated into `<library>/netlists/<cell>.mac` and played back
with `Tools > Playback Macro...`.

Verified: the macro is written, parsed by ADS and executed (ADS opens the
schematic view for the cell). **Not yet verified:** the component-placement
calls place 0 items when run outside an IFF import session - `de_iff_add_component`
requires the IFF symbol map (`de_iff_initialize_import`), so the remaining
work is either (a) driving the palette + canvas directly through the GUI, or
(b) generating an IFF import file.

---
`tools/netlist_sim.py` - AC netlist solver (modified nodal analysis)

Supported: R, C, L, V, I, E (VCVS), G (VCCS), SPICE + ADS value suffixes

Validated against analytic results:

- VCVS divider: 0.0 dB (expected 0 dB)
- RC cutoff: -3.01 dB (expected -3.01 dB)
- Series RLC at resonance: -14.48 dB (analytic -14.63 dB)
- BJT small-signal: 9.15 dB (analytic gm*R_c = 9.25 dB)

Used by `sim_lna.py` (AC sweep + plot) and `lna_optimize.py` (network
optimisation against the solver).

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
- `POST /hfss/build` - accepts a saved `design` name, or derives a parameter
  set from the request and builds from it (the parameter set comes back with
  the result)

CLI:

```
python tools/interface.py design-params --name patch_2p4ghz_fr4 --frequency-ghz 2.4 --substrate FR4
python tools/interface.py list-designs
python tools/interface.py build-antenna --design patch_2p4ghz_fr4
```

Web UI: panel "1. Design Parameters (set before building)" -> derive and
save, then "2. Build Antenna in HFSS" (inline or from a saved set).

Saved sets live in `projects/designs/*.json`.

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

GET  /ads/status

GET  /ads/launch

POST /ads/build

GET  /hfss/new_project

POST /hfss/create_antenna

POST /hfss/build_patch

POST /hfss/build_monopole

POST /hfss/build_dipole

POST /hfss/build_yagi_prototype

POST /hfss/build

---

# Updates (v0.3.0)

- HFSS generators kept geometry-only (no excitation/setup/sweep automation).
- Active circuit phase: Class AB audio power amplifier designed and verified (50 W RMS, 8 ohm, +/-35 V, A_v = 101).
- ADS circuit build command layer added (`/ads/build`, tools/ads.py).
- FastAPI unified build commands added: `/hfss/build` (antenna) and `/ads/build` (circuit).

# Current Challenges

1. Lumped-port automation (HFSS) - parked, manual in HFSS later
2. Reliable HFSS excitation creation - parked, manual later
3. Automatic solver setup generation - parked, manual later
4. Frequency sweep generation - parked, manual later
5. HFSS result extraction - parked, manual later
6. ADS COM programmatic circuit build - unavailable, substituted with MATLAB design math

---

# Next Priorities

## Priority 1

ADS Active/Passive Circuit Builds

Goals:

- Author ADS circuit from FastAPI command (`/ads/build`)
- Passive matching networks for HFSS antennas
- Active amplifier stages (LNA / PA) for HFSS antennas

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

---

# Repository Status

Current Milestone:

v0.3.0

Major Features Completed:

- HFSS COM Integration
- FastAPI Backend
- Patch Generator
- Monopole Generator
- Dipole Generator
- Yagi Prototype Generator
- ADS Launch / Build Command Layer
- FastAPI `/ads/build` + `/hfss/build` Commands
- Class AB Audio Power Amplifier Design

---

# Handoff Instructions

If another AI continues this project:

1. Read README.md
2. Read PROJECT_STATE.md
3. Review backend/app.py
4. Review tools/hfss_com.py
5. Review tools/ads.py

Then continue with:

- ADS circuit build implementation (post-COM)
- Passive matching networks
- LNA / PA designs
- S11 / gain extraction
- Optimization engine

The Yagi dimensions are currently provisional and should be validated against the original HFSS tutorial before production use.

Author: Michael Antwi
