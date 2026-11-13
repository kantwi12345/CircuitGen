# CircuitGen

CircuitGen is a programmable HFSS + ADS automation platform that generates
antenna geometries in Ansys Electronics Desktop (HFSS) and builds
active/passive circuits in Keysight ADS, driven through a FastAPI backend,
a CLI, and a web UI.

The system uses PyWin32 COM automation for HFSS and a generated ADS
workspace/netlist/build-sheet flow for ADS (ADS has no COM automation
interface on this machine — verified experimentally).

## Features

### HFSS automation
- Automatic HFSS project and design creation
- Automatic geometry generation (patch, monopole, dipole, Yagi-Uda)
- Radiation boundary + perfect-E boundaries
- Geometry-only build path (excitation, analysis setup and frequency
  sweep are configured manually in HFSS later)
- Design parameters: set frequency/substrate/thickness first, then derive
  the full geometry (feed width, feed length, board size, air box)
- Design variables written into HFSS's Local Variables table
- Automated geometry validation (build + query HFSS at multiple frequencies)

### ADS automation
- ADS launch + workspace generation (real ADS 2023 format, cloned from a
  reference workspace)
- Per-design local library with `.oalib`, netlist, build sheet, AEL macro,
  design report
- Active designs: Class AB Audio Power Amplifier (50 W / 8 Ω / ±35 V),
  PA output stage, LNA (2.4 GHz)
- Passive designs: 50 Ω → 36.5 Ω impedance matching network
- LNA synthesis with computed, numerically verified matching networks
- AEL macro generation + playback (via pywinauto GUI automation)
- AC netlist simulator (MNA-based, validated 4/4 against analytic results)

### FastAPI interface
- `/hfss/build` — build an antenna (patch / monopole / dipole / yagi)
- `/ads/build` — build a circuit (passive / active)
- `/design/params`, `/design/build` — HFSS design parameters
- `/ads/design/params`, `/ads/design/build` — ADS circuit design parameters
- `/ads/status`, `/ads/launch` — ADS status and launch
- `/tools`, `/health`, `/design` — discovery and Claude integration

### CLI + Web UI
- `tools/interface.py` — `build-antenna`, `build-circuit`, `design-params`,
  `list-designs`, `ads-design-params`, `ads-list-designs`,
  `ads-build-circuit`, `--open-ads`
- Web UI at `http://127.0.0.1:8000/ui/` — set design parameters and
  trigger builds with one click

## Supported antennas

### Patch Antenna
- FR4 / Rogers5880 / Rogers4350B substrates
- 50 Ω microstrip feed (feed width from Hammerstad synthesis)
- Parametric feed length (λ0/8), board size, radiation box
- Substrate material auto-selected per substrate

### Monopole Antenna
- Quarter-wave radiator (λ0/4)
- Ground plane and radiation box scale with λ0
- Feed gap port sheet at the base

### Dipole Antenna
- Half-wave radiator (λ0/2)
- Feed gap with embedded port sheet
- Radiation box scales with λ0

### Yagi-Uda Antenna (Prototype)
- Reflector, driven element, 3 directors, boom, feed cone
- Dimensions are provisional (validate against the original HFSS tutorial)

## Supported circuits

### Class AB Audio Power Amplifier
- 50 W RMS into 8 Ω, ±35 V dual rail
- Closed-loop gain 101 (40.09 dB)
- Zobel + supply decoupling
- Verified: V_RMS = 20 V, V_PEAK = 28.28 V, I_PEAK = 3.54 A

### LNA (2.4 GHz)
- 15 dB gain, S11 −20.2 dB, 82.3 MHz BW, NF est. 1.34 dB
- Input: C_pad 0.95 pF + L_sig 8.56 nH, output: π network (C_o1 0.97 pF, L_out 5.44 nH, C_o2 4.93 pF)
- Bias: R_E 330 Ω, R_B1 16 kΩ, R_B2 11 kΩ

### PA (push-pull output stage)
- Class AB complementary pair, 50 W into 8 Ω

### Impedance Matching Network
- 50 Ω → 36.5 Ω L-match (quarter-wave monopole over ground)
- Verified: Zin = 49.89 − 0.21j Ω, |S11| = −52.6 dB

## Technology stack

### Backend
- Python 3.9+
- FastAPI
- Pydantic
- Uvicorn

### HFSS interface
- PyWin32 (COM)
- Ansys Electronics Desktop 2022 R1
- HFSS

### ADS interface
- Keysight ADS 2023 Update 1 (no COM automation — GUI-driven)
- pywinauto (UIA backend) for GUI automation

### Simulation
- MATLAB R2025b (design math, synthesis)
- Custom MNA AC netlist solver (`tools/netlist_sim.py`)
- scikit-rf / PySpice (when available)

## Project structure

```text
CircuitGen
│
├── backend
│   └── app.py                 # FastAPI backend (HFSS + ADS + design params)
│
├── tools
│   ├── hfss_com.py            # HFSS geometry generators
│   ├── patch_builder.py       # Parametric patch generator
│   ├── antenna_calcs.py       # patch_dimensions, patch_layout, monopole_layout, dipole_layout, microstrip_width_50ohm
│   ├── antenna_library.py     # SUBSTRATES (FR4, Rogers5880, Rogers4350B)
│   ├── hfss_vars.py           # HFSS Local Variables (GUI automation)
│   ├── design_params.py       # HFSS design parameters (set before building)
│   ├── ads.py                 # ADS status / launch / build
│   ├── ads_project.py         # ADS workspace generation (real ADS 2023 format)
│   ├── ads_schematic.py       # ADS schematic build sheet generator
│   ├── ads_ael.py             # ADS AEL macro generator (placement)
│   ├── ads_attach.py          # ADS GUI automation (workspace attach + cell creation)
│   ├── ads_design.py          # ADS circuit design parameters
│   ├── netlist_sim.py         # AC netlist simulator (MNA)
│   ├── hfss_sim.py            # HFSS simulation automation (excitation, setup, sweep, solve, results)
│   ├── hfss_launch.py         # HFSS launch helper
│   ├── hfss_project.py        # HFSS project helper
│   └── interface.py           # CLI build interface
│
├── static
│   └── index.html             # Web build interface (served at /ui/)
│
├── draw_schematic.py          # Class AB PA schematic diagram generator
├── draw_lna_schematic.py      # LNA schematic diagram generator
├── draw_matching_schematic.py # Impedance matching network schematic diagram
├── lna_synthesis.py           # LNA synthesis with scipy solvers
├── lna_optimize.py            # LNA optimisation loop
├── sim_lna.py                 # LNA AC simulation + plot
├── validate_antennas.py       # Geometry validator (builds in HFSS, checks)
│
├── projects
│   ├── designs/               # saved HFSS + ADS design parameter sets
│   ├── Class_AB_Audio_Power_Amplifier/   # workspace artifacts + schematic.png
│   ├── LNA/                   # workspace artifacts + schematic.png + AC_RESULTS.png
│   ├── PA/                    # workspace artifacts
│   └── Impedance_Matching_Network/       # workspace artifacts + schematic.png
│
├── results                    # generated simulation results
├── backend
│   └── app.py                 # FastAPI backend
├── PROJECT_STATE.md
├── PROJECT_NOTES.md
├── README.md
├── .gitignore
└── requirements.txt
```

## Getting started

### Prerequisites
- Python 3.9+
- Ansys Electronics Desktop 2022 R1 (HFSS) with a valid license
- Keysight ADS 2023 Update 1 (for circuit builds)
- (Optional) MATLAB R2025b for design math

### Installation
```bash
cd C:\CircuitGen
python -m venv venv
venv\Scripts\pip install -r requirements.txt
venv\Scripts\pip install pywinauto comtypes
```

### Running the backend
```bash
venv\Scripts\python.exe -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```
Open `http://127.0.0.1:8000/ui/` for the web interface, or `http://127.0.0.1:8000/docs` for Swagger.

### Building an antenna in HFSS
```bash
# CLI
python tools/interface.py build-antenna --antenna-type patch --frequency-ghz 2.4

# Or set design parameters first
python tools/interface.py design-params --name my_patch --frequency-ghz 5.2 --substrate Rogers4350B
python tools/interface.py build-antenna --design my_patch
```

### Building a circuit in ADS
```bash
python tools/interface.py ads-design-params --name pa_50w_8ohm --design "Class AB Audio Power Amplifier"
python tools/interface.py ads-build-circuit --design pa_50w_8ohm --open-ads
```

### Validating antenna geometry
```bash
python validate_antennas.py
```

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/tools` | List available tools |
| POST | `/design` | Ask Claude (AI) a question |
| POST | `/design/params` | Set HFSS design parameters |
| GET | `/design/params` | List saved HFSS designs |
| GET | `/design/params/{name}` | Load a saved HFSS design |
| POST | `/design/build` | Build HFSS antenna from a saved design |
| GET | `/ads/status` | ADS installation status |
| GET | `/ads/launch` | Launch ADS |
| POST | `/ads/design/params` | Set ADS circuit design parameters |
| GET | `/ads/design/params` | List saved ADS designs |
| GET | `/ads/design/params/{name}` | Load a saved ADS design |
| POST | `/ads/design/build` | Build ADS circuit from a saved design |
| POST | `/ads/build` | Build ADS circuit (inline) |
| GET | `/hfss/new_project` | Create a new HFSS project |
| POST | `/hfss/create_antenna` | Create antenna geometry (layout preview) |
| POST | `/hfss/build_patch` | Build patch antenna in HFSS |
| POST | `/hfss/build_monopole` | Build monopole antenna in HFSS |
| POST | `/hfss/build_dipole` | Build dipole antenna in HFSS |
| POST | `/hfss/build_yagi_prototype` | Build Yagi-Uda prototype in HFSS |
| POST | `/hfss/build` | Build antenna (generic command) |

## Notes

- **HFSS excitation, analysis setup and frequency sweep** are configured manually in HFSS after geometry generation (geometry-only mode).
- **ADS COM automation** is not available on this machine — verified experimentally. Workspaces are generated on disk and attached via the GUI (or the `--open-ads` automation).
- **Yagi-Uda dimensions** are provisional and should be validated against the original HFSS tutorial before production use.
- **LNA device parameters** are assumed (BFP420-class) and must be replaced with real datasheet values.
- **Impedance matching network** load impedance (36.5 Ω) is assumed for a quarter-wave monopole over ground.

## Author

Michael Antwi
