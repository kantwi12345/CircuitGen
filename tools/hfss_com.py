import os

import pythoncom
import win32com.client

from tools import hfss_sim
from tools.antenna_calcs import (
    patch_dimensions,
    patch_layout,
    monopole_layout,
    dipole_layout,
)


# --------------------------------------------------------------------------
# port definitions
#
# Each antenna generator creates a "PortSheet" rectangle that spans the gap
# between the ground plane and the driven conductor. The lumped port is
# placed on that sheet; the integration line is derived from the real sheet
# geometry because HFSS rejects a port whose line misses the sheet.
# --------------------------------------------------------------------------

PATCH_PORT = {"sheet": "PortSheet", "impedance": 50}

MONOPOLE_PORT = {"sheet": "PortSheet", "impedance": 50}

DIPOLE_PORT = {"sheet": "PortSheet", "impedance": 50}

YAGI_PORT = {"sheet": "PortSheet", "impedance": 50}


def _run_simulation(
    design,
    project,
    port,
    frequency_ghz,
    results_dir,
    project_path=None,
    port_count=1,
    solve=True,
    span_ghz=0.5,
    sweep_count=101,
    setup_name="Setup1",
    sweep_name="Sweep1",
):
    """Excite, set up, solve and extract results for a generated antenna."""

    summary = {
        "setup": None,
        "sweep": None,
        "solved": False,
        "results_dir": results_dir,
    }

    port_info = hfss_sim.assign_lumped_port(design, name="LumpedPort1", **port)
    summary["port"] = port_info

    setup = hfss_sim.create_driven_setup(
        design, setup_name, frequency_ghz=frequency_ghz
    )
    summary["setup"] = setup["setup"]

    window = hfss_sim.default_sweep(frequency_ghz, span_ghz, sweep_count)

    sweep = hfss_sim.create_frequency_sweep(
        design,
        setup_name,
        sweep_name,
        start_ghz=window["start_ghz"],
        stop_ghz=window["stop_ghz"],
        count=window["count"],
    )
    summary["sweep"] = sweep["sweep"]

    if project_path:
        try:
            os.makedirs(os.path.dirname(project_path), exist_ok=True)
            project.SaveAs(project_path, True)
            summary["project_path"] = project_path
        except Exception as exc:      # noqa: BLE001 - saving must not abort
            summary["project_save_error"] = str(exc)

    if not solve:
        return summary

    hfss_sim.solve_setup(design, setup_name)
    summary["solved"] = True

    solution = f"{setup_name} : {sweep_name}"

    data = hfss_sim.extract_s_parameters(
        design, solution, results_dir, port_count=port_count
    )
    summary["s_parameters"] = data
    summary["summary"] = hfss_sim.summarise_s_parameters(
        data, frequency_hz=frequency_ghz * 1e9
    )
    summary["resonance_hz"] = hfss_sim.resonant_frequency(data, "S11")

    try:
        summary["antenna_parameters"] = hfss_sim.extract_antenna_parameters(
            design, setup_name
        )
    except Exception as exc:      # noqa: BLE001 - antenna params are optional
        summary["antenna_parameters"] = {"error": str(exc)}

    return summary


def create_project():

    pythoncom.CoInitialize()

    try:

        app = win32com.client.Dispatch(
            "Ansoft.ElectronicsDesktop"
        )

        desktop = app.GetAppDesktop()

        project = desktop.NewProject()

        project.InsertDesign(
            "HFSS",
            "PatchAntenna",
            "DrivenModal",
            ""
        )

        return {
            "status": "HFSS project created"
        }

    finally:
        pythoncom.CoUninitialize()


# --------------------------------------------------------------------------
# build + simulate
# --------------------------------------------------------------------------

DESIGN_NAMES = {
    "patch": "PatchAntenna",
    "monopole": "MonopoleAntenna",
    "dipole": "DipoleAntenna",
    "yagi": "YagiUdaPrototype",
}

PORT_DEFINITIONS = {
    "patch": PATCH_PORT,
    "monopole": MONOPOLE_PORT,
    "dipole": DIPOLE_PORT,
    "yagi": YAGI_PORT,
}

DEFAULT_RESULTS_ROOT = r"C:\CircuitGen\results"


def simulate_antenna(
    antenna_type="monopole",
    frequency_ghz=2.4,
    results_dir=None,
    project_path=None,
    port_count=1,
    span_ghz=0.5,
    sweep_count=101,
    solve=True,
    **build_kwargs,
):
    """Build an antenna, excite it, solve it and extract the S parameters.

    This is the end-to-end entry point: the geometry generator runs first,
    then the lumped port, the driven modal setup and the frequency sweep are
    created, the model is solved and the S parameters are read back.
    """

    key = str(antenna_type).lower()

    if key not in DESIGN_NAMES:
        raise ValueError(
            f"unknown antenna type '{antenna_type}' "
            f"(expected one of {', '.join(sorted(DESIGN_NAMES))})"
        )

    if key == "patch":
        build = create_patch_antenna(
            frequency_ghz=frequency_ghz, **build_kwargs
        )
    elif key == "monopole":
        build = create_monopole_antenna(
            frequency_ghz=frequency_ghz, **build_kwargs
        )
    elif key == "dipole":
        build = create_dipole_antenna(
            frequency_ghz=frequency_ghz, **build_kwargs
        )
    else:
        build = create_yagi_uda_antenna_prototype(
            frequency_ghz=frequency_ghz, **build_kwargs
        )

    # the generators tear COM down when they return, so re-arm it and pick
    # up the design they just created
    pythoncom.CoInitialize()

    app = win32com.client.Dispatch("Ansoft.ElectronicsDesktop")
    desktop = app.GetAppDesktop()

    project, design = hfss_sim.find_design(DESIGN_NAMES[key], desktop)

    if design is None:
        raise RuntimeError(
            f"could not find the '{DESIGN_NAMES[key]}' design in the session"
        )

    if not results_dir:
        results_dir = os.path.join(DEFAULT_RESULTS_ROOT, key)

    os.makedirs(results_dir, exist_ok=True)

    simulation = _run_simulation(
        design,
        project,
        PORT_DEFINITIONS[key],
        frequency_ghz,
        results_dir,
        project_path=project_path,
        port_count=port_count,
        solve=solve,
        span_ghz=span_ghz,
        sweep_count=sweep_count,
    )

    return {
        "antenna_type": key,
        "frequency_ghz": frequency_ghz,
        "build": build,
        "simulation": simulation,
    }


def create_patch_antenna(
    width_mm=None,
    length_mm=None,
    frequency_ghz=2.4,
    thickness_mm=1.6,
    er=4.4,
    substrate="FR4",
):

    """
    Build the microstrip patch antenna.

    All dimensions are derived from the operating frequency and substrate
    (feed width, feed length, board size, port sheet and air box scale
    together), so the geometry stays valid at any frequency.

    The implementation lives in tools/patch_builder.py.
    """

    from tools.patch_builder import (
        create_patch_antenna as _create_patch_antenna
    )

    return _create_patch_antenna(
        width_mm=width_mm,
        length_mm=length_mm,
        frequency_ghz=frequency_ghz,
        thickness_mm=thickness_mm,
        er=er,
        substrate=substrate,
    )


def create_monopole_antenna(frequency_ghz=2.4, use_variables=True):

    """
    Quarter-wave monopole.

    The radiator length follows lambda0/4 and the ground plane and
    radiation box scale with the wavelength, so the model is valid at any
    frequency. The radiator base offset (1 mm along Z) is the validated
    user-specified geometry.
    """

    pythoncom.CoInitialize()

    try:

        layout = monopole_layout(frequency_ghz)

        if layout["checks"]:
            raise ValueError(
                "inconsistent monopole layout: " + "; ".join(layout["checks"])
            )

        app = win32com.client.Dispatch(
            "Ansoft.ElectronicsDesktop"
        )

        desktop = app.GetAppDesktop()

        project = desktop.NewProject()

        project.InsertDesign(
            "HFSS",
            "MonopoleAntenna",
            "DrivenModal",
            ""
        )

        design = project.SetActiveDesign(
            "MonopoleAntenna"
        )

        editor = design.SetActiveEditor(
            "3D Modeler"
        )

        monopole_length = layout["monopole_length_mm"]
        monopole_radius = layout["monopole_radius_mm"]
        ground_half = layout["ground_half_mm"]

        #
        # Ground Plane
        #

        editor.CreateRectangle(
            [
                "NAME:RectangleParameters",
                "IsCovered:=", True,
                "XStart:=", f"-{ground_half}mm",
                "YStart:=", f"-{ground_half}mm",
                "ZStart:=", "0mm",
                "Width:=", f"{2 * ground_half}mm",
                "Height:=", f"{2 * ground_half}mm",
                "WhichAxis:=", "Z"
            ],
            [
                "NAME:Attributes",
                "Name:=", "GroundPlane"
            ]
        )

        #
        # Monopole Radiator
        #

        editor.CreateCylinder(
            [
                "NAME:CylinderParameters",
                "XCenter:=", "0mm",
                "YCenter:=", "0mm",
                "ZCenter:=", "1mm",
                "Radius:=", f"{monopole_radius}mm",
                "Height:=", f"{monopole_length}mm",
                "WhichAxis:=", "Z"
            ],
            [
                "NAME:Attributes",
                "Name:=", "Monopole"
            ]
        )

        editor.AssignMaterial(
            [
                "NAME:Selections",
                "Selections:=", "Monopole"
            ],
            [
                "NAME:Attributes",
                "MaterialValue:=", "\"pec\"",
                "SolveInside:=", False
            ]
        )

        editor.AssignMaterial(
            [
                "NAME:Selections",
                "Selections:=", "GroundPlane"
            ],
            [
                "NAME:Attributes",
                "MaterialValue:=", "\"pec\"",
                "SolveInside:=", False
            ]
        )

        #
        # Port Sheet - feed gap at the base of the radiator
        #

        editor.CreateRectangle(
            [
                "NAME:RectangleParameters",
                "IsCovered:=", True,
                "XStart:=", f"-{monopole_radius}mm",
                "YStart:=", "0mm",
                "ZStart:=", "0mm",
                "Width:=", "1mm",
                "Height:=", f"{2 * monopole_radius}mm",
                "WhichAxis:=", "Y"
            ],
            [
                "NAME:Attributes",
                "Name:=", "PortSheet"
            ]
        )

        #
        # Air Box
        #

        editor.CreateBox(
            [
                "NAME:BoxParameters",
                "XPosition:=", f"{layout['air_x_mm']}mm",
                "YPosition:=", f"{layout['air_y_mm']}mm",
                "ZPosition:=", f"{layout['air_z_mm']}mm",
                "XSize:=", f"{layout['air_size_xy_mm']}mm",
                "YSize:=", f"{layout['air_size_xy_mm']}mm",
                "ZSize:=", f"{layout['air_size_z_mm']}mm"
            ],
            [
                "NAME:Attributes",
                "Name:=", "AirBox"
            ]
        )

        #
        # Radiation Boundary
        #

        boundary_module = design.GetModule(
            "BoundarySetup"
        )

        boundary_module.AssignPerfectE(
            [
                "NAME:PerfE1",
                "Objects:=",
                ["GroundPlane"],
                "InfGroundPlane:=",
                False
            ]
        )

        boundary_module.AssignRadiation(
            [
                "NAME:Rad1",
                "Objects:=",
                ["AirBox"]
            ]
        )

        #
        # Design variables - appear in
        # Properties -> MonopoleAntenna -> Local Variables
        #
        variables = {
            "f0": f"{frequency_ghz}GHz",
            "rad_l": f"{monopole_length}mm",
            "rad_r": f"{monopole_radius}mm",
            "rad_z": "1mm",
            "gnd_half": f"{ground_half}mm",
            "port_x": f"-{monopole_radius}mm",
            "port_w": f"{2 * monopole_radius}mm",
            "air_x": f"{layout['air_x_mm']}mm",
            "air_y": f"{layout['air_y_mm']}mm",
            "air_z": f"{layout['air_z_mm']}mm",
            "air_sx": f"{layout['air_size_xy_mm']}mm",
            "air_sy": f"{layout['air_size_xy_mm']}mm",
            "air_sz": f"{layout['air_size_z_mm']}mm",
        }

        variable_result = {"status": "skipped"}
        if use_variables:
            try:
                from tools.hfss_vars import set_design_variables_isolated

                variable_result = set_design_variables_isolated(
                    variables, design_name="MonopoleAntenna"
                )
            except Exception as exc:
                variable_result = {"status": "failed", "error": str(exc)}

        return {
            "status": "Monopole geometry created",
            "frequency_ghz": frequency_ghz,
            "monopole_length_mm": monopole_length,
            "monopole_radius_mm": monopole_radius,
            "ground_half_mm": ground_half,
            "lambda0_mm": layout["lambda0_mm"],
            "variables": variables,
            "variables_result": variable_result,
            "objects": [
                "GroundPlane",
                "Monopole",
                "PortSheet",
                "AirBox"
            ],
            "boundaries": [
                "PerfE1",
                "Rad1"
            ]
        }

    finally:
        pythoncom.CoUninitialize()


def create_dipole_antenna(frequency_ghz=2.4, use_variables=True):

    """
    Half-wave dipole with a feed gap.

    The radiator length follows lambda0/2 and the radiation box scales with
    the wavelength, so the model is valid at any frequency.
    """

    pythoncom.CoInitialize()

    try:

        layout = dipole_layout(frequency_ghz)

        if layout["checks"]:
            raise ValueError(
                "inconsistent dipole layout: " + "; ".join(layout["checks"])
            )

        app = win32com.client.Dispatch(
            "Ansoft.ElectronicsDesktop"
        )

        desktop = app.GetAppDesktop()

        project = desktop.NewProject()

        project.InsertDesign(
            "HFSS",
            "DipoleAntenna",
            "DrivenModal",
            ""
        )

        design = project.SetActiveDesign(
            "DipoleAntenna"
        )

        editor = design.SetActiveEditor(
            "3D Modeler"
        )

        dipole_length = layout["dipole_length_mm"]
        dipole_radius = layout["dipole_radius_mm"]
        gap_length = layout["gap_length_mm"]
        gap_radius = layout["gap_radius_mm"]

        #
        # Dipole
        #

        editor.CreateCylinder(
            [
                "NAME:CylinderParameters",
                "XCenter:=", "0mm",
                "YCenter:=", "0mm",
                "ZCenter:=", f"{-dipole_length / 2}mm",
                "Radius:=", f"{dipole_radius}mm",
                "Height:=", f"{dipole_length}mm",
                "WhichAxis:=", "Z"
            ],
            [
                "NAME:Attributes",
                "Name:=", "Dipole"
            ]
        )

        editor.AssignMaterial(
            [
                "NAME:Selections",
                "Selections:=", "Dipole"
            ],
            [
                "NAME:Attributes",
                "MaterialValue:=", "\"pec\"",
                "SolveInside:=", False
            ]
        )

        #
        # Cylindrical Feed Gap
        #

        editor.CreateCylinder(
            [
                "NAME:CylinderParameters",
                "XCenter:=", "0mm",
                "YCenter:=", "0mm",
                "ZCenter:=", f"{-gap_length / 2}mm",
                "Radius:=", f"{gap_radius}mm",
                "Height:=", f"{gap_length}mm",
                "WhichAxis:=", "Z"
            ],
            [
                "NAME:Attributes",
                "Name:=", "Gap"
            ]
        )

        #
        # Cut Gap But Keep Gap Body
        #

        editor.Subtract(
            [
                "NAME:Selections",
                "Blank Parts:=", "Dipole",
                "Tool Parts:=", "Gap"
            ],
            [
                "NAME:SubtractParameters",
                "KeepOriginals:=", True
            ]
        )

        #
        # Port Sheet
        #

        editor.CreateRectangle(
            [
                "NAME:RectangleParameters",
                "IsCovered:=", True,
                "XStart:=", f"-{gap_radius}mm",
                "YStart:=", "0mm",
                "ZStart:=", f"-{gap_length / 2}mm",
                "Width:=", f"{gap_length}mm",
                "Height:=", f"{2 * gap_radius}mm",
                "WhichAxis:=", "Y"
            ],
            [
                "NAME:Attributes",
                "Name:=", "PortSheet"
            ]
        )

        #
        # Air Box
        #

        editor.CreateBox(
            [
                "NAME:BoxParameters",
                "XPosition:=", f"{layout['air_x_mm']}mm",
                "YPosition:=", f"{layout['air_y_mm']}mm",
                "ZPosition:=", f"{layout['air_z_mm']}mm",
                "XSize:=", f"{layout['air_size_xy_mm']}mm",
                "YSize:=", f"{layout['air_size_xy_mm']}mm",
                "ZSize:=", f"{layout['air_size_z_mm']}mm"
            ],
            [
                "NAME:Attributes",
                "Name:=", "AirBox"
            ]
        )

        #
        # Radiation Boundary
        #

        boundary_module = design.GetModule(
            "BoundarySetup"
        )

        boundary_module.AssignRadiation(
            [
                "NAME:Rad1",
                "Objects:=",
                ["AirBox"]
            ]
        )

        #
        # Design variables - appear in
        # Properties -> DipoleAntenna -> Local Variables
        #
        variables = {
            "f0": f"{frequency_ghz}GHz",
            "dip_l": f"{dipole_length}mm",
            "dip_r": f"{dipole_radius}mm",
            "gap_l": f"{gap_length}mm",
            "gap_r": f"{gap_radius}mm",
            "port_x": f"-{gap_radius}mm",
            "air_x": f"{layout['air_x_mm']}mm",
            "air_y": f"{layout['air_y_mm']}mm",
            "air_z": f"{layout['air_z_mm']}mm",
            "air_sx": f"{layout['air_size_xy_mm']}mm",
            "air_sy": f"{layout['air_size_xy_mm']}mm",
            "air_sz": f"{layout['air_size_z_mm']}mm",
        }

        variable_result = {"status": "skipped"}
        if use_variables:
            try:
                from tools.hfss_vars import set_design_variables_isolated

                variable_result = set_design_variables_isolated(
                    variables, design_name="DipoleAntenna"
                )
            except Exception as exc:
                variable_result = {"status": "failed", "error": str(exc)}

        return {
            "status": "Dipole geometry created",
            "frequency_ghz": frequency_ghz,
            "dipole_length_mm": dipole_length,
            "dipole_radius_mm": dipole_radius,
            "gap_length_mm": gap_length,
            "gap_radius_mm": gap_radius,
            "lambda0_mm": layout["lambda0_mm"],
            "variables": variables,
            "variables_result": variable_result,
            "objects": [
                "Dipole",
                "Gap",
                "PortSheet",
                "AirBox"
            ],
            "boundaries": [
                "Rad1"
            ]
        }

    finally:
        pythoncom.CoUninitialize()


def create_yagi_uda_antenna_prototype(frequency_ghz=2.5):

    pythoncom.CoInitialize()

    try:

        app = win32com.client.Dispatch(
            "Ansoft.ElectronicsDesktop"
        )

        desktop = app.GetAppDesktop()

        project = desktop.NewProject()

        project.InsertDesign(
            "HFSS",
            "YagiUdaPrototype",
            "DrivenModal",
            ""
        )

        design = project.SetActiveDesign(
            "YagiUdaPrototype"
        )

        editor = design.SetActiveEditor(
            "3D Modeler"
        )

        #
        # ==========================================
        # PROVISIONAL PARAMETERS
        # ==========================================
        #

        element_radius = 1.0

        reflector_length = 63.6
        driven_length = 57.6

        director1_length = 54.0
        director2_length = 52.8
        director3_length = 51.6

        reflector_x = 0.0
        driven_x = 24.0

        director1_x = 42.0
        director2_x = 60.0
        director3_x = 78.0

        gap_radius = 1.05
        gap_length = 1.0

        boom_radius = 1.0
        boom_length = 100.0

        cone_height = 15.0
        cone_large_radius = 6.0
        cone_small_radius = 1.05

        #
        # ==========================================
        # STAGE 1 - YAGI ELEMENTS
        # ==========================================
        #

        def make_element(name, xpos, length):

            editor.CreateCylinder(
                [
                    "NAME:CylinderParameters",
                    "XCenter:=", f"{xpos}mm",
                    "YCenter:=", "0mm",
                    "ZCenter:=", f"-{length/2}mm",
                    "Radius:=", f"{element_radius}mm",
                    "Height:=", f"{length}mm",
                    "WhichAxis:=", "Z"
                ],
                [
                    "NAME:Attributes",
                    "Name:=", name
                ]
            )

        make_element(
            "Reflector",
            reflector_x,
            reflector_length
        )

        make_element(
            "DrivenElement",
            driven_x,
            driven_length
        )

        make_element(
            "Director1",
            director1_x,
            director1_length
        )

        make_element(
            "Director2",
            director2_x,
            director2_length
        )

        make_element(
            "Director3",
            director3_x,
            director3_length
        )

        #
        # ==========================================
        # STAGE 2 - FEED GEOMETRY
        # ==========================================
        #

        editor.CreateCylinder(
            [
                "NAME:CylinderParameters",
                "XCenter:=", f"{driven_x}mm",
                "YCenter:=", "0mm",
                "ZCenter:=", f"-{gap_length/2}mm",
                "Radius:=", f"{gap_radius}mm",
                "Height:=", f"{gap_length}mm",
                "WhichAxis:=", "Z"
            ],
            [
                "NAME:Attributes",
                "Name:=", "FeedGap"
            ]
        )

        editor.Subtract(
            [
                "NAME:Selections",
                "Blank Parts:=", "DrivenElement",
                "Tool Parts:=", "FeedGap"
            ],
            [
                "NAME:SubtractParameters",
                "KeepOriginals:=", True
            ]
        )

        editor.CreateRectangle(
            [
                "NAME:RectangleParameters",
                "IsCovered:=", True,

                "XStart:=", f"{driven_x-gap_radius}mm",
                "YStart:=", "0mm",
                "ZStart:=", f"-{gap_length/2}mm",

                "Width:=", f"{2*gap_radius}mm",
                "Height:=", f"{gap_length}mm",

                "WhichAxis:=", "Y"
            ],
            [
                "NAME:Attributes",
                "Name:=", "PortSheet"
            ]
        )

        #
        # ==========================================
        # STAGE 3 - BOOM
        # ==========================================
        #

        editor.CreateCylinder(
            [
                "NAME:CylinderParameters",
                "XCenter:=", "0mm",
                "YCenter:=", "0mm",
                "ZCenter:=", "0mm",
                "Radius:=", f"{boom_radius}mm",
                "Height:=", f"{boom_length}mm",
                "WhichAxis:=", "X"
            ],
            [
                "NAME:Attributes",
                "Name:=", "Boom"
            ]
        )

        #
        # ==========================================
        # STAGE 4 - FEED CONE
        # ==========================================
        #

        editor.CreateCone(
            [
                "NAME:ConeParameters",

                "XCenter:=", f"{driven_x-cone_height}mm",
                "YCenter:=", "0mm",
                "ZCenter:=", "0mm",

                "WhichAxis:=", "X",

                "BottomRadius:=", f"{cone_large_radius}mm",
                "TopRadius:=", f"{cone_small_radius}mm",
                "Height:=", f"{cone_height}mm"
            ],
            [
                "NAME:Attributes",
                "Name:=", "FeedCone"
            ]
        )

        #
        # AIR BOX
        #

        editor.CreateBox(
            [
                "NAME:BoxParameters",
                "XPosition:=", "-80mm",
                "YPosition:=", "-100mm",
                "ZPosition:=", "-100mm",
                "XSize:=", "220mm",
                "YSize:=", "200mm",
                "ZSize:=", "200mm"
            ],
            [
                "NAME:Attributes",
                "Name:=", "AirBox"
            ]
        )

        #
        # RADIATION BOUNDARY
        #

        boundary_module = design.GetModule(
            "BoundarySetup"
        )

        boundary_module.AssignRadiation(
            [
                "NAME:Rad1",
                "Objects:=",
                ["AirBox"]
            ]
        )



        for _obj in ["Reflector", "DrivenElement", "Director1", "Director2", "Director3", "Boom", "FeedCone"]:
            editor.AssignMaterial(
                [
                    "NAME:Selections",
                    "Selections:=", _obj
                ],
                [
                    "NAME:Attributes",
                    "MaterialValue:=", "\"pec\"",
                    "SolveInside:=", False
                ]
            )

        return {
            "status": "Yagi-Uda prototype geometry created",
            "frequency_ghz": frequency_ghz,
            "note": "Prototype dimensions are assumed and should be tuned.",
            "objects": [
                "Reflector",
                "DrivenElement",
                "FeedGap",
                "PortSheet",
                "Director1",
                "Director2",
                "Director3",
                "Boom",
                "FeedCone",
                "AirBox"
            ]
        }

    finally:
        pythoncom.CoUninitialize()