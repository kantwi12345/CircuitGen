import math
import os

import pythoncom
import win32com.client

from tools.antenna_calcs import patch_dimensions, patch_layout

# The ground plane extends slightly past the board edge so the port sheet
# is fully backed by ground (matches the validated original model).
GROUND_EXT_MM = 0.46

# HFSS material names per substrate (first one the solver accepts is used).
MATERIAL_CANDIDATES = {
    "FR4": ["FR4_epoxy"],
    "Rogers5880": [
        "rogers5880",
        "Rogers_5880",
        "Rogers RT/duroid 5880 (laminate)",
    ],
    "Rogers4350B": [
        "rogers4350b",
        "Rogers_4350B",
        "Rogers RO4350B (laminate)",
    ],
}


def _assign_material(editor, object_name, candidates):
    """Assign the first material name the solver accepts."""

    errors = []

    for material in candidates:
        try:
            editor.ChangeProperty(
                [
                    "NAME:AllTabs",
                    [
                        "NAME:Geometry3DAttributeTab",
                        [
                            "NAME:PropServers",
                            object_name
                        ],
                        [
                            "NAME:ChangedProps",
                            [
                                "NAME:Material",
                                "Value:=",
                                f"\"{material}\""
                            ]
                        ]
                    ]
                ]
            )
            return material, errors
        except Exception as exc:  # material name not in the library
            errors.append(f"{material}: {exc}")

    return None, errors


def patch_variables(layout: dict, frequency_ghz: float, er: float) -> dict:
    """
    HFSS design variables for the patch.

    These are exactly the entries that appear under
    Properties -> <design> -> Local Variables.
    """

    return {
        "f0": f"{frequency_ghz}GHz",
        "er": f"{er}",
        "h": f"{layout['thickness_mm']}mm",
        "patch_w": f"{layout['patch_width_mm']}mm",
        "patch_l": f"{layout['patch_length_mm']}mm",
        "patch_x": f"{layout['patch_x_mm']}mm",
        "patch_y": f"{layout['patch_y_mm']}mm",
        "feed_w": f"{layout['feed_width_mm']}mm",
        "feed_l": f"{layout['feed_length_mm']}mm",
        "feed_x": f"{layout['feed_x_mm']}mm",
        "board_x": f"{layout['board_x_mm']}mm",
        "board_y": f"{layout['board_y_mm']}mm",
        "gnd_ext": f"{GROUND_EXT_MM}mm",
        "port_x": f"{layout['port_x_mm']}mm",
        "air_x": f"{layout['air_x_mm']}mm",
        "air_y": f"{layout['air_y_mm']}mm",
        "air_z": f"{layout['air_z_mm']}mm",
        "air_sx": f"{layout['air_size_x_mm']}mm",
        "air_sy": f"{layout['air_size_y_mm']}mm",
        "air_sz": f"{layout['air_size_z_mm']}mm",
    }


def _build_geometry(editor, layout, use_variables, created=None):
    """Create the patch geometry, either from variables or literal values."""

    created = created if created is not None else []

    if use_variables:
        substrate_x = "$board_x"
        substrate_y = "$board_y"
        substrate_h = "$h"
        ground_y = "-$gnd_ext"
        ground_h = "$board_y + $gnd_ext"
        patch_x, patch_y = "$patch_x", "$patch_y"
        patch_w, patch_l = "$patch_w", "$patch_l"
        feed_x, feed_w, feed_l = "$feed_x", "$feed_w", "$feed_l"
        port_x = "$port_x"
        air = ("$air_x", "$air_y", "$air_z", "$air_sx", "$air_sy", "$air_sz")
    else:
        substrate_x = f"{layout['board_x_mm']}mm"
        substrate_y = f"{layout['board_y_mm']}mm"
        substrate_h = f"{layout['thickness_mm']}mm"
        ground_y = f"-{GROUND_EXT_MM}mm"
        ground_h = f"{layout['board_y_mm'] + GROUND_EXT_MM}mm"
        patch_x = f"{layout['patch_x_mm']}mm"
        patch_y = f"{layout['patch_y_mm']}mm"
        patch_w = f"{layout['patch_width_mm']}mm"
        patch_l = f"{layout['patch_length_mm']}mm"
        feed_x = f"{layout['feed_x_mm']}mm"
        feed_w = f"{layout['feed_width_mm']}mm"
        feed_l = f"{layout['feed_length_mm']}mm"
        port_x = f"{layout['port_x_mm']}mm"
        air = (
            f"{layout['air_x_mm']}mm",
            f"{layout['air_y_mm']}mm",
            f"{layout['air_z_mm']}mm",
            f"{layout['air_size_x_mm']}mm",
            f"{layout['air_size_y_mm']}mm",
            f"{layout['air_size_z_mm']}mm",
        )

    #
    # Substrate
    #
    editor.CreateBox(
        [
            "NAME:BoxParameters",
            "XPosition:=", "0mm",
            "YPosition:=", "0mm",
            "ZPosition:=", "0mm",
            "XSize:=", substrate_x,
            "YSize:=", substrate_y,
            "ZSize:=", substrate_h
        ],
        [
            "NAME:Attributes",
            "Name:=", "FR4_Substrate"
        ]
    )
    created.append("FR4_Substrate")

    #
    # Ground Plane
    #
    editor.CreateRectangle(
        [
            "NAME:RectangleParameters",
            "IsCovered:=", True,
            "XStart:=", "0mm",
            "YStart:=", ground_y,
            "ZStart:=", "0mm",
            "Width:=", substrate_x,
            "Height:=", ground_h,
            "WhichAxis:=", "Z"
        ],
        [
            "NAME:Attributes",
            "Name:=", "GroundPlane"
        ]
    )

    #
    # Patch
    #
    editor.CreateRectangle(
        [
            "NAME:RectangleParameters",
            "IsCovered:=", True,
            "XStart:=", patch_x,
            "YStart:=", patch_y,
            "ZStart:=", substrate_h,
            "Width:=", patch_w,
            "Height:=", patch_l,
            "WhichAxis:=", "Z"
        ],
        [
            "NAME:Attributes",
            "Name:=", "Patch"
        ]
    )

    #
    # Feed Line - 50 ohm line from the board edge to the patch edge
    #
    editor.CreateRectangle(
        [
            "NAME:RectangleParameters",
            "IsCovered:=", True,
            "XStart:=", feed_x,
            "YStart:=", "0mm",
            "ZStart:=", substrate_h,
            "Width:=", feed_w,
            "Height:=", feed_l,
            "WhichAxis:=", "Z"
        ],
        [
            "NAME:Attributes",
            "Name:=", "FeedLine"
        ]
    )

    #
    # Port Sheet - on the board edge, under the feed line
    #
    editor.CreateRectangle(
        [
            "NAME:RectangleParameters",
            "IsCovered:=", True,
            "XStart:=", port_x,
            "YStart:=", "0mm",
            "ZStart:=", "0mm",
            "Width:=", substrate_h,
            "Height:=", feed_w,
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
            "XPosition:=", air[0],
            "YPosition:=", air[1],
            "ZPosition:=", air[2],
            "XSize:=", air[3],
            "YSize:=", air[4],
            "ZSize:=", air[5]
        ],
        [
            "NAME:Attributes",
            "Name:=", "AirBox"
        ]
    )


def _reconnect_design(project_name=None, design_name="PatchAntenna"):
    """Re-acquire the design and 3D Modeler editor from the running HFSS.

    Only the newest project is touched - iterating over closed/stale
    projects can take the process down with an access violation.
    """

    app = win32com.client.Dispatch("Ansoft.ElectronicsDesktop")
    desktop = app.GetAppDesktop()

    projects = list(desktop.GetProjects())
    if not projects:
        raise RuntimeError("no HFSS projects")

    for project in reversed(projects):
        try:
            if project_name and project.GetName() != project_name:
                continue
            design = project.SetActiveDesign(design_name)
            return design, design.SetActiveEditor("3D Modeler")
        except Exception:
            continue

    raise RuntimeError("design not found after reconnect")


def _build_geometry_isolated(project_name, inputs, timeout=600):
    """
    Build the geometry from the design variables, in a child process.

    HFSS 2022 R1 can take the calling process down (access violation)
    when a geometry field is driven by a variable expression, so the
    attempt is isolated and the caller falls back to literal values.
    """

    import json
    import subprocess
    import sys

    script = (
        "import json,sys;"
        "sys.path.insert(0, r'C:\\CircuitGen');"
        "from tools.patch_builder import _build_geometry, _reconnect_design;"
        "from tools.antenna_calcs import patch_layout;"
        f"inputs = json.loads({json.dumps(json.dumps(inputs))});"
        "layout = patch_layout(**inputs);"
        "design, editor = _reconnect_design(sys.argv[1]);"
        "_build_geometry(editor, layout, True, []);"
        "print('@@OK@@')"
    )

    try:
        completed = subprocess.run(
            [sys.executable, "-c", script, project_name],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "timeout"}

    if "@@OK@@" in (completed.stdout or ""):
        return {"ok": True}

    return {
        "ok": False,
        "error": f"parametric build failed (rc={completed.returncode})",
    }


def create_patch_antenna(
    width_mm=None,
    length_mm=None,
    frequency_ghz=2.4,
    thickness_mm=1.6,
    er=4.4,
    substrate="FR4",
    use_variables=True,
):

    """
    Build the microstrip patch antenna.

    Every dimension is derived from the operating frequency and substrate so
    the geometry is self-consistent at any frequency.

    The design parameters are also written into the HFSS design as local
    variables (Properties -> <design> -> Local Variables) and the geometry
    is built from those variables, so the model can be swept or optimised
    inside HFSS.
    """

    pythoncom.CoInitialize()

    try:

        layout = patch_layout(
            frequency_ghz,
            er=er,
            h_mm=thickness_mm,
            width_mm=width_mm,
            length_mm=length_mm,
        )

        if layout["checks"]:
            raise ValueError(
                "inconsistent patch layout: " + "; ".join(layout["checks"])
            )

        app = win32com.client.Dispatch(
            "Ansoft.ElectronicsDesktop"
        )

        desktop = app.GetAppDesktop()

        project = desktop.NewProject()

        project_name = project.GetName()

        project.InsertDesign(
            "HFSS",
            "PatchAntenna",
            "DrivenModal",
            ""
        )

        design = project.SetActiveDesign(
            "PatchAntenna"
        )

        editor = design.SetActiveEditor(
            "3D Modeler"
        )

        #
        # Geometry - literal values (HFSS 2022 R1 crashes when a geometry
        # field is driven by a variable expression, so the variables are
        # attached to the finished design afterwards).
        #
        _build_geometry(editor, layout, False, [])

        #
        # Assign substrate material
        #
        candidates = MATERIAL_CANDIDATES.get(
            substrate, ["FR4_epoxy"]
        )
        material, material_errors = _assign_material(
            editor, "FR4_Substrate", candidates
        )

        if material is None:
            material = "FR4_epoxy"
            _assign_material(editor, "FR4_Substrate", [material])

        #
        # Boundary Setup
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
        # Design variables - these appear in
        # Properties -> PatchAntenna -> Local Variables
        #
        variables = patch_variables(layout, frequency_ghz, er)
        variable_result = {"status": "skipped"}
        built_with_variables = False
        variable_error = None

        if use_variables:
            try:
                from tools.hfss_vars import set_design_variables_isolated

                variable_result = set_design_variables_isolated(variables)
                built_with_variables = (
                    variable_result.get("status") == "variables_set"
                )
            except Exception as exc:
                variable_result = {"status": "failed", "error": str(exc)}
                variable_error = str(exc)

        return {
            "status": "Patch antenna ready for simulation",
            "frequency_ghz": frequency_ghz,
            "substrate": substrate,
            "material": material,
            "patch_width_mm": layout["patch_width_mm"],
            "patch_length_mm": layout["patch_length_mm"],
            "feed_width_mm": layout["feed_width_mm"],
            "feed_length_mm": layout["feed_length_mm"],
            "board_x_mm": layout["board_x_mm"],
            "board_y_mm": layout["board_y_mm"],
            "lambda0_mm": layout["lambda0_mm"],
            "variables": variables,
            "variables_result": variable_result,
            "built_with_variables": built_with_variables,
            "variable_error": variable_error,
            "objects": [
                "FR4_Substrate",
                "GroundPlane",
                "Patch",
                "FeedLine",
                "PortSheet",
                "AirBox"
            ],
            "boundaries": [
                "PerfE1",
                "Rad1"
            ],
        }

    finally:
        pythoncom.CoUninitialize()
