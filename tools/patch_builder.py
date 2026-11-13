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

    Every dimension is derived from the operating frequency and substrate so
    the geometry is self-consistent at any frequency (feed width, feed
    length, board size, port sheet and air box all scale together).
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

        substrate_x = layout["board_x_mm"]
        substrate_y = layout["board_y_mm"]
        substrate_h = layout["thickness_mm"]

        #
        # FR4 Substrate
        #
        editor.CreateBox(
            [
                "NAME:BoxParameters",
                "XPosition:=", "0mm",
                "YPosition:=", "0mm",
                "ZPosition:=", "0mm",
                "XSize:=", f"{substrate_x}mm",
                "YSize:=", f"{substrate_y}mm",
                "ZSize:=", f"{substrate_h}mm"
            ],
            [
                "NAME:Attributes",
                "Name:=", "FR4_Substrate"
            ]
        )

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
        # Ground Plane
        #
        editor.CreateRectangle(
            [
                "NAME:RectangleParameters",
                "IsCovered:=", True,
                "XStart:=", "0mm",
                "YStart:=", f"-{GROUND_EXT_MM}mm",
                "ZStart:=", "0mm",
                "Width:=", f"{substrate_x}mm",
                "Height:=", f"{substrate_y + GROUND_EXT_MM}mm",
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
                "XStart:=", f"{layout['patch_x_mm']}mm",
                "YStart:=", f"{layout['patch_y_mm']}mm",
                "ZStart:=", f"{substrate_h}mm",
                "Width:=", f"{layout['patch_width_mm']}mm",
                "Height:=", f"{layout['patch_length_mm']}mm",
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
                "XStart:=", f"{layout['feed_x_mm']}mm",
                "YStart:=", "0mm",
                "ZStart:=", f"{substrate_h}mm",
                "Width:=", f"{layout['feed_width_mm']}mm",
                "Height:=", f"{layout['feed_length_mm']}mm",
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
                "XStart:=", f"{layout['port_x_mm']}mm",
                "YStart:=", "0mm",
                "ZStart:=", "0mm",
                "Width:=", f"{layout['thickness_mm']}mm",
                "Height:=", f"{layout['feed_width_mm']}mm",
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
                "XSize:=", f"{layout['air_size_x_mm']}mm",
                "YSize:=", f"{layout['air_size_y_mm']}mm",
                "ZSize:=", f"{layout['air_size_z_mm']}mm"
            ],
            [
                "NAME:Attributes",
                "Name:=", "AirBox"
            ]
        )

        #
        # Boundary Setup
        #
        boundary_module = design.GetModule(
            "BoundarySetup"
        )

        #
        # Perfect E on Ground Plane
        #
        boundary_module.AssignPerfectE(
            [
                "NAME:PerfE1",
                "Objects:=",
                ["GroundPlane"],
                "InfGroundPlane:=",
                False
            ]
        )

        #
        # Radiation Boundary
        #
        boundary_module.AssignRadiation(
            [
                "NAME:Rad1",
                "Objects:=",
                ["AirBox"]
            ]
        )

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


