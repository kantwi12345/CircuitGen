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
        # FR4 substrate
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
        # Ground Plane
        #
        editor.CreateRectangle(
            [
                "NAME:RectangleParameters",
                "IsCovered:=", True,
                "XStart:=", "0mm",
                "YStart:=", "0mm",
                "ZStart:=", "0mm",
                "Width:=", f"{substrate_x}mm",
                "Height:=", f"{substrate_y}mm",
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

        return {
            "status": "Patch antenna with air box created",
            "patch_width_mm": width_mm,
            "patch_length_mm": length_mm
        }

    finally:
        pythoncom.CoUninitialize()
