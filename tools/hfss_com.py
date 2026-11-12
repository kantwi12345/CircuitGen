import pythoncom
import win32com.client


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
def create_patch_antenna(width_mm, length_mm):

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

        design = project.SetActiveDesign(
            "PatchAntenna"
        )

        editor = design.SetActiveEditor(
            "3D Modeler"
        )

        substrate_x = 60
        substrate_y = 60
        substrate_h = 1.6

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
        # Assign FR4 material to substrate
        #
        editor.ChangeProperty(
            [
                "NAME:AllTabs",
                [
                    "NAME:Geometry3DAttributeTab",
                    [
                        "NAME:PropServers",
                        "FR4_Substrate"
                    ],
                    [
                        "NAME:ChangedProps",
                        [
                            "NAME:Material",
                            "Value:=",
                            "\"FR4_epoxy\""
                        ]
                    ]
                ]
            ]
        )

        #
        # Ground Plane
        #
        editor.CreateRectangle(
            [
                "NAME:RectangleParameters",
                "IsCovered:=", True,
                "XStart:=", "0mm",
                "YStart:=", "-0.46mm",
                "ZStart:=", "0mm",
                "Width:=", f"{substrate_x}mm",
                "Height:=", f"{substrate_y + 0.46}mm",
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
        patch_x = (substrate_x - width_mm) / 2
        patch_y = (substrate_y - length_mm) / 2

        editor.CreateRectangle(
            [
                "NAME:RectangleParameters",
                "IsCovered:=", True,
                "XStart:=", f"{patch_x}mm",
                "YStart:=", f"{patch_y}mm",
                "ZStart:=", f"{substrate_h}mm",
                "Width:=", f"{width_mm}mm",
                "Height:=", f"{length_mm}mm",
                "WhichAxis:=", "Z"
            ],
            [
                "NAME:Attributes",
                "Name:=", "Patch"
            ]
        )
          
                #
        # Feed Line
        #

        feed_width = 3.0
        feed_x = 28.5
        feed_y = 0.0
        feed_length = 16.0

        editor.CreateRectangle(
            [
                "NAME:RectangleParameters",
                "IsCovered:=", True,
                "XStart:=", "28.5mm",
                "YStart:=", "0mm",
                "ZStart:=", "1.6mm",
                "Width:=", "3mm",
                "Height:=", "16mm",
                "WhichAxis:=", "Z"
            ],
            [
                "NAME:Attributes",
                "Name:=", "FeedLine"
            ]
               )
    
        # Port Sheet
        #

        editor.CreateRectangle(
            [
                "NAME:RectangleParameters",
                "IsCovered:=", True,
                "XStart:=", "28.5mm",
                "YStart:=", "0mm",
                "ZStart:=", "0mm",
                "Width:=", "1.6mm",
                "Height:=", "3mm",
                "WhichAxis:=", "Y"
            ],
            [
                "NAME:Attributes",
                "Name:=", "PortSheet"
            ]
        )
        
        # Air Box
        #
        editor.CreateBox(
            [
                "NAME:BoxParameters",
                "XPosition:=", "-40mm",
                "YPosition:=", "-40mm",
                "ZPosition:=", "-40mm",
                "XSize:=", "140mm",
                "YSize:=", "140mm",
                "ZSize:=", "120mm"
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

        #
        # Lumped Port
        #


        #
        # Analysis Setup
        #

        return {
            "status": "Patch antenna ready for simulation",
            "patch_width_mm": width_mm,
            "patch_length_mm": length_mm,
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

def create_monopole_antenna(frequency_ghz=2.4):

    pythoncom.CoInitialize()

    try:

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

        #
        # Dimensions
        #

        monopole_length = 31.25
        monopole_radius = 0.5

        #
        # Ground Plane
        #

        editor.CreateRectangle(
            [
                "NAME:RectangleParameters",
                "IsCovered:=", True,
                "XStart:=", "-50mm",
                "YStart:=", "-50mm",
                "ZStart:=", "0mm",
                "Width:=", "100mm",
                "Height:=", "100mm",
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
        # Port Sheet
        #

        editor.CreateRectangle(
            [
                "NAME:RectangleParameters",
                "IsCovered:=", True,
                "XStart:=", "-0.5mm",
                "YStart:=", "0mm",
                "ZStart:=", "0mm",
                "Width:=", "1mm",
                "Height:=", "1mm",
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
                "XPosition:=", "-100mm",
                "YPosition:=", "-100mm",
                "ZPosition:=", "-100mm",
                "XSize:=", "200mm",
                "YSize:=", "200mm",
                "ZSize:=", "250mm"
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



        return {
            "status": "Monopole geometry created",
            "frequency_ghz": frequency_ghz,
            "monopole_length_mm": monopole_length,
            "objects": [
                "GroundPlane",
                "Monopole",
                "PortSheet",
                "AirBox"
            ]
        }

    finally:
        pythoncom.CoUninitialize()
def create_dipole_antenna(frequency_ghz=2.4):

    pythoncom.CoInitialize()

    try:

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

        #
        # Dipole Parameters
        #

        dipole_length = 62.5
        dipole_radius = 1.0

        gap_length = 1.0
        gap_radius = 1.0

        #
        # Dipole
        #

        editor.CreateCylinder(
            [
                "NAME:CylinderParameters",
                "XCenter:=", "0mm",
                "YCenter:=", "0mm",
                "ZCenter:=", "-31.25mm",
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
                "ZCenter:=", "-0.5mm",
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
        # Same dimensions as gap.
        #

        editor.CreateRectangle(
            [
                "NAME:RectangleParameters",
                "IsCovered:=", True,

                "XStart:=", f"-{gap_radius}mm",
                "YStart:=", "0mm",
                "ZStart:=", f"-{gap_length/2}mm",

                "Width:=", f"{gap_length}mm",
                "Height:=", f"{2*gap_radius}mm",

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
                "XPosition:=", "-100mm",
                "YPosition:=", "-100mm",
                "ZPosition:=", "-100mm",
                "XSize:=", "200mm",
                "YSize:=", "200mm",
                "ZSize:=", "250mm"
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



        return {
            "status": "Dipole geometry created",
            "frequency_ghz": frequency_ghz,
            "dipole_length_mm": dipole_length,
            "dipole_radius_mm": dipole_radius,
            "gap_length_mm": gap_length,
            "gap_radius_mm": gap_radius,
            "port_width_mm": 2 * gap_radius,
            "port_height_mm": gap_length,
            "objects": [
                "Dipole",
                "Gap",
                "PortSheet",
                "AirBox"
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