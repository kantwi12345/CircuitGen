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

## ADS Build Flow (mirrors the HFSS flow)

Per design:

- Workspace: `C:\CircuitGen\projects\<Design_Name>`
- Component-level netlist: `<Design_Name>.net`
- `README.txt` with ADS import/simulation steps

Designs available:

- Active: `Class AB Audio Power Amplifier`, `PA`, `LNA`
- Passive: `Impedance Matching Network`

Verification:

- L-match (50 ohm -> 36.5 ohm @ 2.4 GHz): Zin = 49.89 - 0.21j ohm, |S11| = 0.0024 (-52.6 dB)
- LNA (2.4 GHz): optimised + simulated -> Av = 16.11 dB, S11 = -20.20 dB,
  -3 dB BW = 82.3 MHz (2.336-2.418 GHz), NF estimate 1.34 dB (assumed F_min)

---

## Circuit Simulation Substitute

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
