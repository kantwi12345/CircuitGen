# CircuitGen

CircuitGen is a programmable HFSS automation platform that generates
antenna geometries in Ansys Electronics Desktop (HFSS), driven through a
FastAPI backend, a CLI, and a web UI.

The system uses PyWin32 COM automation for HFSS (geometry generation,
design parameters, validation).

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

### FastAPI interface
- `/hfss/build` — build an antenna (patch / monopole / dipole / yagi)
- `/design/params`, `/design/build` — HFSS design parameters
- `/tools`, `/health`, `/design` — discovery and Claude integration

### CLI + Web UI
- `tools/interface.py` — `build-antenna`, `design-params`, `list-designs`
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

### Simulation
- MATLAB R2025b (design math, synthesis)
- scikit-rf / PySpice (when available)

## Project structure

```text
CircuitGen
│
├── backend
│   └── app.py                 # FastAPI backend (HFSS + design params)
│
├── tools
│   ├── hfss_com.py            # HFSS geometry generators
│   ├── patch_builder.py       # Parametric patch generator
│   ├── antenna_calcs.py       # patch_dimensions, patch_layout, monopole_layout, dipole_layout, microstrip_width_50ohm
│   ├── antenna_library.py     # SUBSTRATES (FR4, Rogers5880, Rogers4350B)
│   ├── hfss_vars.py           # HFSS Local Variables (GUI automation)
│   ├── design_params.py       # HFSS design parameters (set before building)
│   ├── hfss_sim.py            # HFSS simulation automation (excitation, setup, sweep, solve, results)
│   ├── hfss_launch.py         # HFSS launch helper
│   ├── hfss_project.py        # HFSS project helper
│   └── interface.py           # CLI build interface
│
├── static
│   └── index.html             # Web build interface (served at /ui/)
│
├── validate_antennas.py       # Geometry validator (builds in HFSS, checks)
│
├── projects
│   └── designs/               # saved HFSS design parameter sets
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
| GET | `/hfss/new_project` | Create a new HFSS project |
| POST | `/hfss/create_antenna` | Create antenna geometry (layout preview) |
| POST | `/hfss/build_patch` | Build patch antenna in HFSS |
| POST | `/hfss/build_monopole` | Build monopole antenna in HFSS |
| POST | `/hfss/build_dipole` | Build dipole antenna in HFSS |
| POST | `/hfss/build_yagi_prototype` | Build Yagi-Uda prototype in HFSS |
| POST | `/hfss/build` | Build antenna (generic command) |

## Notes

- **HFSS excitation, analysis setup and frequency sweep** are configured manually in HFSS after geometry generation (geometry-only mode).
- **Yagi-Uda dimensions** are provisional and should be validated against the original HFSS tutorial before production use.

## Author

Michael Antwi