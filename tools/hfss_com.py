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

        design = project.SetActiveDesign(
            "PatchAntenna"
        )

        editor = design.SetActiveEditor(
            "3D Modeler"
        )

        editor.CreateBox(
            [
                "NAME:BoxParameters",
                "XPosition:=", "0mm",
                "YPosition:=", "0mm",
                "ZPosition:=", "0mm",
                "XSize:=", "20mm",
                "YSize:=", "20mm",
                "ZSize:=", "2mm"
            ],
            [
                "NAME:Attributes",
                "Name:=", "TestBox"
            ]
        )

        return {
            "status": "HFSS project, design and geometry created"
        }


    finally:
        pythoncom.CoUninitialize()
def create_patch_antenna(width_mm, length_mm):

    pythoncom.CoInitialize()

    try:

        return {
            "width_mm": width_mm,
            "length_mm": length_mm,
            "status": "Patch antenna generator placeholder"
        }

    finally:
        pythoncom.CoUninitialize()
