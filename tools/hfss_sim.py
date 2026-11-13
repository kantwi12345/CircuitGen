"""
CircuitGen - HFSS simulation automation (excitation, setup, sweep, solve, results).

The geometry generators in ``tools/hfss_com.py`` stop at the model. This
module drives the rest of the HFSS workflow through the pywin32 COM API:

    BoundarySetup.AssignLumpedPort      -> port excitation
    AnalysisSetup.InsertSetup           -> driven modal setup
    AnalysisSetup.InsertFrequencySweep  -> frequency sweep
    design.Analyze                      -> solve
    ReportSetup.CreateReport            -> S-parameter report
    ReportSetup.ExportToFile            -> .tab export
    Solutions.GetAntennaParameters      -> gain / directivity / efficiency

Signatures below were read from the live HFSS 2022.1 type information, so
the call shapes match the installed product rather than a guess.
"""

import math
import os

import pythoncom
import win32com.client


# --------------------------------------------------------------------------
# session helpers
# --------------------------------------------------------------------------


def connect_desktop():
    """Connect to the running AEDT desktop and return (app, desktop).

    The generators call ``CoUninitialize`` when they return, so COM has to be
    re-armed before the session can be used again.
    """

    pythoncom.CoInitialize()

    app = win32com.client.Dispatch("Ansoft.ElectronicsDesktop")

    return app, app.GetAppDesktop()


def find_design(design_name, desktop=None):
    """Locate the most recent design with a given name.

    ``GetActiveProject`` is not reliable right after a generator returns, so
    every project is searched instead. The last match wins because the
    generators reuse the same design names.
    """

    if desktop is None:
        _, desktop = connect_desktop()

    found = (None, None)

    for project in desktop.GetProjects():
        try:
            designs = project.GetDesigns()
        except Exception:      # noqa: BLE001 - skip unreadable projects
            continue

        for design in designs:
            try:
                if design.GetName() == design_name:
                    found = (project, design)
            except Exception:  # noqa: BLE001 - skip unreadable designs
                continue

    return found


def open_project(path, desktop=None):
    """Open an AEDT project, reusing it when it is already open.

    AEDT refuses to open a project twice, and a crash leaves a stale lock
    file behind, so both cases are handled here.
    """

    if desktop is None:
        _, desktop = connect_desktop()

    target = os.path.normcase(os.path.abspath(path))
    target_dir = os.path.normcase(os.path.dirname(target))

    for project in desktop.GetProjects():
        try:
            current = os.path.normcase(os.path.abspath(project.GetPath()))
        except Exception:      # noqa: BLE001 - skip unreadable projects
            continue

        # GetPath returns the project folder, not the .aedt file
        if current in (target, target_dir):
            return project

    lock = path + ".lock"
    if os.path.exists(lock):
        try:
            os.remove(lock)
        except OSError:
            pass

    return desktop.OpenProject(path)


def last_error(desktop=None):
    """Return the last error message from the AEDT message manager.

    The COM exception raised by a failed call carries no text, so the
    message manager is the only place the real reason shows up.
    """

    if desktop is None:
        _, desktop = connect_desktop()

    try:
        messages = list(desktop.GetMessages("", "", 2))
    except Exception:      # noqa: BLE001 - the message manager is optional
        return ""

    if not messages:
        return ""

    return str(messages[-1])


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------


def _num(value):
    """Format a number for an HFSS property list."""

    if isinstance(value, bool):
        return "true" if value else "false"

    if isinstance(value, str):
        return value

    if isinstance(value, int):
        return str(value)

    if isinstance(value, float):
        if value == int(value) and abs(value) < 1e15:
            return str(int(value))
        return repr(value)

    return str(value)


def _mm(value):
    """Format a length in millimetres for HFSS."""

    return f"{float(value):g}mm"


def _ghz(value):
    """Format a frequency in GHz for HFSS."""

    return f"{float(value):g}GHz"


def _hz(value_hz):
    """Format a frequency in Hz for HFSS (used by sweep exports)."""

    return f"{float(value_hz):g}Hz"


# --------------------------------------------------------------------------
# excitation
# --------------------------------------------------------------------------


def sheet_geometry(editor, sheet_name):
    """Return (face id, corner positions) of a sheet object.

    Positions are returned as floats in the model units (mm).
    """

    face = list(editor.GetFaceIDsOfSheet(sheet_name))[0]

    vertices = list(editor.GetVertexIDsFromFace(face))

    positions = []
    for vertex in vertices:
        raw = list(editor.GetVertexPosition(vertex))
        positions.append([float(value) for value in raw])

    return face, positions


def integration_line(positions, axis="Z"):
    """Build a port line that lies on the sheet.

    HFSS rejects a lumped port whose integration line does not lie on the
    port sheet, so the line is derived from the real sheet extents instead
    of from the nominal drawing parameters.

    ``axis`` is the direction the port spans (the sheet normal is the
    remaining axis).
    """

    if not positions:
        raise ValueError("the port sheet has no geometry")

    if axis.upper() == "Z":
        index = 2
    elif axis.upper() == "X":
        index = 0
    else:
        raise ValueError(f"unsupported port axis: {axis}")

    other = [i for i in range(3) if i != index]

    mid = [
        (min(p[i] for p in positions) + max(p[i] for p in positions)) / 2.0
        for i in other
    ]

    spans = sorted(p[index] for p in positions)

    start = [0.0, 0.0, 0.0]
    end = [0.0, 0.0, 0.0]

    for slot, coordinate in zip(other, mid):
        start[slot] = coordinate
        end[slot] = coordinate

    start[index] = spans[0]
    end[index] = spans[-1]

    return tuple(start), tuple(end)


def assign_lumped_port(
    design,
    name="LumpedPort1",
    sheet="PortSheet",
    start=None,
    end=None,
    impedance=50.0,
    axis="Z",
):
    """Assign a lumped port on a sheet.

    The port sheet is expected to span the gap between the two conductors
    (ground plane and radiator). The integration line is taken from the real
    sheet geometry; ``start``/``end`` can override it when needed.
    """

    editor = design.SetActiveEditor("3D Modeler")

    face, positions = sheet_geometry(editor, sheet)

    if start is None or end is None:
        start, end = integration_line(positions, axis=axis)

    module = design.GetModule("BoundarySetup")

    module.AssignLumpedPort([
        f"NAME:{name}",
        "Faces:=", [int(face)],
        "DoDeembed:=", False,
        "RenormalizeAllTerminals:=", True,
        [
            "NAME:Modes",
            [
                "NAME:Mode1",
                "ModeNum:=", 1,
                "UseIntLine:=", True,
                [
                    "NAME:IntLine",
                    "Start:=", [_mm(start[0]), _mm(start[1]), _mm(start[2])],
                    "End:=", [_mm(end[0]), _mm(end[1]), _mm(end[2])],
                ],
                "AlignmentGroup:=", 0,
                "CharImp:=", "Zpi",
                "RenormImp:=", f"{_num(impedance)}ohm",
            ],
        ],
        "ShowReporterFilter:=", False,
        "ReporterFilter:=", [True],
        "Impedance:=", f"{_num(impedance)}ohm",
    ])

    return {
        "name": name,
        "face": int(face),
        "start": start,
        "end": end,
        "impedance": impedance,
    }


def assign_perfect_e(design, name="PerfE1", objects=()):
    """Assign a perfect-E boundary (ground plane) to the given objects."""

    module = design.GetModule("BoundarySetup")
    module.AssignPerfectE([
        f"NAME:{name}",
        "Objects:=", list(objects),
        "InfGroundPlane:=", False,
    ])
    return name


def assign_radiation(design, name="Rad1", objects=()):
    """Assign a radiation boundary to the given objects (air box faces)."""

    module = design.GetModule("BoundarySetup")
    module.AssignRadiation([
        f"NAME:{name}",
        "Objects:=", list(objects),
        "IsFssReference:=", False,
        "IsFssReferenceArray:=", False,
        "Name:=", name,
    ])
    return name


# --------------------------------------------------------------------------
# analysis setup
# --------------------------------------------------------------------------


def _setup_properties(
    frequency_ghz,
    max_delta_s,
    max_passes,
    mesh_options,
):
    """Build the 'Properties' block of a driven modal setup."""

    properties = [
        "NAME:Properties",
        "Enabled:=", True,
        "SetupType:=", "HFSSDriven",
        "Frequency:=", _ghz(frequency_ghz),
        "MaxDeltaS:=", max_delta_s,
        "UseMatrixConv:=", False,
        "MaximumPasses:=", max_passes,
        "MinimumPasses:=", 1,
        "MinimumConvergedPasses:=", 1,
        "PercentRefinement:=", 30,
        "IsEnabled:=", True,
        "BasisOrder:=", 1,
        "DoLambdaRefine:=", True,
        "DoMaterialLambda:=", True,
        "SetLambdaTarget:=", False,
        "Target:=", 0.3333,
        "UseMaxTetIncrease:=", False,
        "PortAccuracy:=", 2,
        "UseABCOnPort:=", False,
        "SetPortMinMaxTri:=", False,
        "MinTrianglesForPort:=", 100,
    ]

    if mesh_options:
        properties = properties[:2] + ["MeshOptions:=", mesh_options] + properties[2:]

    return properties


def _mesh_options(max_delta_s, max_passes):
    """Mesh controls for a driven modal setup."""

    return [
        "NAME:MeshOptions",
        "MeshType:=", "Auto",
        "MaxDeltaS:=", max_delta_s,
        "MaxPasses:=", max_passes,
        "CurvatureRefinement:=", 1,
        "CurvatureRefinementFactor:=", 2,
        "MinCurvatureRadius:=", 0,
        "CurvatureEnable:=", False,
        "UseCurvature:=", False,
        "UseMaxTetIncrease:=", False,
        "MaxTetIncrease:=", 0.1,
        "MinSurfTetIncrease:=", 0.1,
        "LimitSurfaceMesh:=", False,
        "SurfaceMeshSize:=", 0,
        "EnableMLM:=", True,
        "MLMGrad:=", 0.5,
        "IgnoreDetailSettings:=", False,
        "Regularization:=", 0,
        "SetQuality:=", 2,
        "AutoMaxLength:=", 1e-06,
        "AutoMaxLength2:=", 1e-06,
        "AutoMESH:=", False,
        "AdditionalSetup:=", [
            "NAME:AdditionalSetup",
            "Enable:=", False,
            "MaxLy:=", 3,
        ],
    ]


def create_driven_setup(
    design,
    setup_name="Setup1",
    frequency_ghz=2.4,
    max_delta_s=0.1,
    max_passes=10,
    setup_type="HFSSDriven",
):
    """Create a driven modal analysis setup.

    ``InsertSetup`` takes the *setup type* as its first argument and the
    setup name travels inside the payload, which is why the legacy
    ``InsertSetup("Setup1", ...)`` form is rejected by AEDT.

    HFSS is strict about the property set it accepts, so the payload is
    tried from richest to leanest and the first one that HFSS accepts wins.
    The accepted setup is read back so the caller can confirm it exists.
    """

    module = design.GetModule("AnalysisSetup")

    candidates = [
        [
            f"NAME:{setup_name}",
            "Properties:=", _setup_properties(
                frequency_ghz, max_delta_s, max_passes,
                _mesh_options(max_delta_s, max_passes),
            ),
        ],
        [
            f"NAME:{setup_name}",
            "Properties:=", _setup_properties(
                frequency_ghz, max_delta_s, max_passes, None,
            ),
        ],
    ]

    last_error = None

    for payload in candidates:
        try:
            module.InsertSetup(setup_type, payload)
            setups = list(module.GetSetups() or [])
            if setup_name in setups:
                return {"setup": setup_name, "setups": setups}
            last_error = RuntimeError(
                f"HFSS created {setups} instead of '{setup_name}'"
            )
        except Exception as exc:      # noqa: BLE001 - try the next payload
            last_error = exc

    raise RuntimeError(
        f"HFSS rejected the driven setup '{setup_name}': {last_error}"
    )


def create_frequency_sweep(
    design,
    setup_name="Setup1",
    sweep_name="Sweep1",
    start_ghz=2.0,
    stop_ghz=3.0,
    count=101,
    range_type="LinearCount",
):
    """Create an interpolating frequency sweep inside a setup."""

    module = design.GetModule("AnalysisSetup")

    properties = [
        f"NAME:{sweep_name}",
        "IsEnabled:=", True,
        "RangeType:=", range_type,
        "RangeStart:=", _ghz(start_ghz),
        "RangeEnd:=", _ghz(stop_ghz),
        "RangeCount:=", int(count),
        "Type:=", "Interpolating",
        "SaveFields:=", False,
        "SaveRadFields:=", False,
        "ExtrapToDC:=", False,
        "InterpUseS:=", True,
        "InterpUsePortImped:=", False,
        "InterpUsePropConst:=", True,
        "UseDerivativeConvergence:=", False,
        "InterpDerivTolerance:=", 0.2,
        "UseFullBasis:=", True,
        "EnforcePassivity:=", True,
        "PassivityErrorTolerance:=", 0.0001,
    ]

    errors = []

    for args in (
        (setup_name, properties),
        (setup_name, sweep_name, properties),
    ):
        try:
            module.InsertFrequencySweep(*args)
            sweeps = list(module.GetSweeps(setup_name) or [])
            if not sweeps or sweep_name in sweeps:
                return {"setup": setup_name, "sweep": sweep_name,
                        "sweeps": sweeps}
        except Exception as exc:      # noqa: BLE001 - try the other call shape
            errors.append(exc)

    raise RuntimeError(
        f"HFSS rejected the frequency sweep '{sweep_name}': {errors[-1]}"
    )


def solve_setup(design, setup_name="Setup1", timeout_s=3600):
    """Solve an analysis setup and return the solver messages.

    AEDT dies during a solve when the model is broken, which surfaces as an
    RPC failure rather than a clean error, so the failure is reported with
    the last AEDT message attached.
    """

    try:
        design.Analyze(setup_name)
    except Exception as exc:      # noqa: BLE001 - fall back to the module call
        try:
            module = design.GetModule("AnalysisSetup")
            module.SolveSetup(setup_name)
        except Exception:
            raise RuntimeError(
                f"HFSS could not solve '{setup_name}': {exc} "
                f"(last AEDT message: {last_error()})"
            )

    try:
        messages = list(design.GetModule("Solutions").GetValidISolutionList(True))
    except Exception:
        messages = []

    return {"setup": setup_name, "solutions": messages}


# --------------------------------------------------------------------------
# results
# --------------------------------------------------------------------------


def create_report(
    design,
    report_name,
    expression,
    solution,
    report_type="Modal Solution Data",
    display_type="Rectangular Plot",
    context="Sweep",
):
    """Create a rectangular plot report for a single expression.

    The AEDT call takes seven positional arguments; the named value pairs
    travel as lists, not as separate positional arguments.
    """

    module = design.GetModule("ReportSetup")

    module.CreateReport(
        report_name,
        report_type,
        display_type,
        solution,
        context,
        ["Freq:=", "All"],
        ["X Component:=", "Freq", "Y Component:=", [expression]],
    )

    return report_name


def export_report(design, report_name, path):
    """Export a report to a .tab file and return the path."""

    module = design.GetModule("ReportSetup")

    os.makedirs(os.path.dirname(path), exist_ok=True)

    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass

    module.ExportToFile(report_name, path, False)

    return path


def parse_report_file(path):
    """Parse a HFSS .tab export into frequencies and traces.

    The export looks like::

        Freq (GHz)   dB(S(1,1))
        2.000000E+09 -2.2642528E+01
    """

    frequencies = []
    traces = {}
    header = []

    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        lines = handle.read().splitlines()

    for line in lines:
        stripped = line.strip()

        if not stripped:
            continue

        parts = stripped.replace("\t", " ").split()

        try:
            frequency = float(parts[0])
        except (ValueError, IndexError):
            if "Freq" in stripped and not header:
                header = stripped.split()
            continue

        frequencies.append(frequency)

        for index, value in enumerate(parts[1:]):
            name = header[index + 1] if len(header) > index + 1 else \
                f"trace_{index}"
            try:
                traces.setdefault(name, []).append(float(value))
            except ValueError:
                traces.setdefault(name, []).append(None)

    return {
        "frequencies_hz": frequencies,
        "traces": traces,
        "header": header,
    }


def read_solution_data(
    design,
    expression,
    solution,
    context="Sweep",
    report_type="Modal Solution Data",
):
    """Read the sweep data of one expression straight out of HFSS.

    Exporting a report to a file is unreliable in this AEDT build (the
    export silently produces nothing), so the numbers are pulled from the
    solution data object instead. That object wants the expression as a
    plain string and the sweep values with ``bSIvalue`` set for hertz.
    """

    module = design.GetModule("ReportSetup")

    result = module.GetSolutionDataPerVariation(
        report_type, solution, context, ["Freq:=", "All"], expression,
    )

    data = result[0] if isinstance(result, (list, tuple)) else result

    expressions = [str(item) for item in data.GetDataExpressions()]
    sweep_names = [str(item) for item in data.GetSweepNames()]

    frequencies = []
    if sweep_names:
        frequencies = [
            float(value)
            for value in data.GetSweepValues(sweep_names[0], True)
        ]

    values = []
    errors = []

    for candidate in (expressions[0] if expressions else expression, expression):
        try:
            raw = data.GetRealDataValues(candidate, False)
        except Exception as exc:      # noqa: BLE001 - try the next spelling
            errors.append(exc)
            continue

        if not raw:
            continue

        first = raw[0] if isinstance(raw[0], (list, tuple)) else raw
        values = [float(value) for value in first]
        break

    if not values and errors:
        raise RuntimeError(
            f"HFSS returned no data for '{expression}': {errors[-1]}"
        )

    return {
        "expression": expressions[0] if expressions else expression,
        "frequencies_hz": frequencies,
        "values": values,
    }


def extract_s_parameters(
    design,
    solution,
    out_dir,
    port_count=1,
    prefix="S",
):
    """Extract every Sij of a solution and return the parsed data.

    Both the linear magnitude and the decibel form of each parameter are
    collected, because the summary and the resonance search work in dB.
    """

    os.makedirs(out_dir, exist_ok=True)

    results = {}

    for i in range(1, port_count + 1):
        for j in range(1, port_count + 1):
            label = f"{prefix}{i}{j}"
            expression = f"S({i},{j})"

            traces = {}

            for name, expr in (
                (expression, expression),
                (f"dB({expression})", f"dB({expression})"),
            ):
                try:
                    data = read_solution_data(design, expr, solution)
                except Exception as exc:      # noqa: BLE001 - per parameter
                    traces[name] = None
                    results.setdefault(label, {
                        "expression": expression,
                        "frequencies_hz": [],
                        "traces": {},
                        "errors": {},
                    })["errors"][name] = str(exc)
                    continue

                traces[name] = data["values"]

                if "frequencies_hz" not in results.get(label, {}):
                    results[label] = {
                        "expression": expression,
                        "frequencies_hz": data["frequencies_hz"],
                        "traces": {},
                        "errors": {},
                    }

                results[label]["traces"][name] = data["values"]

            if label not in results:
                results[label] = {
                    "expression": expression,
                    "frequencies_hz": [],
                    "traces": {},
                    "errors": {},
                }

    return results


def extract_antenna_parameters(design, setup_name="Setup1"):
    """Read the antenna parameter summary (gain, directivity, efficiency)."""

    module = design.GetModule("Solutions")

    raw = module.GetAntennaParameters(setup_name)

    return _normalise_antenna_parameters(raw)


def _normalise_antenna_parameters(raw):
    """Turn whatever GetAntennaParameters returns into a flat dict."""

    result = {}

    if raw is None:
        return result

    if isinstance(raw, str):
        raw = [raw]

    try:
        items = list(raw)
    except TypeError:
        items = [raw]

    for item in items:
        if isinstance(item, (list, tuple)):
            for sub in item:
                _store_antenna_parameter(result, sub)
        else:
            _store_antenna_parameter(result, item)

    return result


def _store_antenna_parameter(result, item):
    """Store one 'name: value' antenna parameter line."""

    if item is None:
        return

    if isinstance(item, (list, tuple)):
        if len(item) >= 2:
            result[str(item[0]).strip()] = item[1]
        return

    text = str(item)

    if ":" not in text:
        result[text.strip()] = text.strip()
        return

    key, _, value = text.partition(":")
    result[key.strip()] = value.strip()


def _trace_values(data, prefer_db=True):
    """Pick the trace to summarise (decibels when available)."""

    traces = data.get("traces") or {}

    if not traces:
        return [], []

    if prefer_db:
        for name in traces:
            if name.lower().startswith("db("):
                return traces[name], data.get("frequencies_hz") or []

    name = next(iter(traces))
    return traces[name], data.get("frequencies_hz") or []


def summarise_s_parameters(results, frequency_hz=None):
    """Pick the value of every S parameter at a given frequency.

    The value at the requested frequency is reported, or the worst match
    over the sweep when no frequency is given.
    """

    summary = {}

    for label, data in results.items():
        values, frequencies = _trace_values(data)

        if not frequencies or not values:
            continue

        if frequency_hz is not None:
            index = min(
                range(len(frequencies)),
                key=lambda i: abs(frequencies[i] - frequency_hz),
            )
        else:
            index = min(
                (i for i, v in enumerate(values) if v is not None),
                key=lambda i: values[i],
                default=None,
            )

        if index is None:
            continue

        summary[label] = {
            "frequency_hz": frequencies[index],
            "value_db": values[index],
        }

    return summary


def resonant_frequency(results, label="S11"):
    """Interpolate the frequency where the dB trace reaches its minimum."""

    data = results.get(label)

    if not data:
        return None

    values, frequencies = _trace_values(data)

    if not frequencies or not values:
        return None

    points = [
        (f, v) for f, v in zip(frequencies, values) if v is not None
    ]

    if len(points) < 3:
        return points[0][0] if points else None

    best = min(points, key=lambda item: item[1])
    index = points.index(best)

    if index == 0 or index == len(points) - 1:
        return best[0]

    f0, v0 = points[index - 1]
    f1, v1 = points[index + 1]

    if v1 == v0:
        return best[0]

    # parabola through the three points
    denominator = (f0 - f1) * (f0 - best[0]) * (f1 - best[0])
    if denominator == 0:
        return best[0]

    a = (f1 * (v0 - v1) + f0 * (v1 - v0) + best[0] * (v0 - v1)) / denominator
    b = (
        (f1 ** 2 * (v0 - v1) + f0 ** 2 * (v1 - v0) + best[0] ** 2 * (v0 - v1))
        / denominator
    )

    if a == 0:
        return best[0]

    return -b / (2 * a)


def default_sweep(frequency_ghz, span_ghz=0.5, count=101):
    """Sweep window centred on a design frequency."""

    half = span_ghz / 2.0

    return {
        "start_ghz": max(frequency_ghz - half, 0.01),
        "stop_ghz": frequency_ghz + half,
        "count": count,
    }
