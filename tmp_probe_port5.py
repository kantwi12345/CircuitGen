"""Throwaway: find the working lumped-port payload variant."""

import pythoncom
import win32com.client

pythoncom.CoInitialize()
try:
    app = win32com.client.Dispatch("Ansoft.ElectronicsDesktop")
    desktop = app.GetAppDesktop()

    project = desktop.NewProject()
    project.InsertDesign("HFSS", "PortProbe5", "DrivenModal", "")
    design = project.SetActiveDesign("PortProbe5")
    editor = design.SetActiveEditor("3D Modeler")

    editor.CreateBox(
        ["NAME:BoxParameters",
         "XPosition:=", "0mm", "YPosition:=", "0mm", "ZPosition:=", "0mm",
         "XSize:=", "20mm", "YSize:=", "20mm", "ZSize:=", "1mm"],
        ["NAME:Attributes", "Name:=", "Ground"],
    )
    editor.CreateBox(
        ["NAME:BoxParameters",
         "XPosition:=", "5mm", "YPosition:=", "0mm", "ZPosition:=", "1mm",
         "XSize:=", "10mm", "YSize:=", "20mm", "ZSize:=", "1mm"],
        ["NAME:Attributes", "Name:=", "Strip"],
    )
    editor.CreateRectangle(
        ["NAME:RectangleParameters",
         "IsCovered:=", True,
         "XStart:=", "8mm", "YStart:=", "0mm", "ZStart:=", "0mm",
         "Width:=", "4mm", "Height:=", "1mm",
         "WhichAxis:=", "Y"],
        ["NAME:Attributes", "Name:=", "PortSheet"],
    )

    module = design.GetModule("BoundarySetup")
    face = list(editor.GetFaceIDs("PortSheet"))[0]

    def modes():
        return ["NAME:Modes",
                ["NAME:Mode1",
                 "ModeNum:=", 1,
                 "UseIntLine:=", True,
                 ["NAME:IntLine",
                  "Coordinate System:=", "Global",
                  "Start:=", ["10mm", "0mm", "0mm"],
                  "End:=", ["10mm", "0mm", "1mm"]],
                 "AlignmentGroup:=", 0,
                 "CharImp:=", "Zpi",
                 "RenormImp:=", "50ohm"]]

    variants = {
        "faces int + modes": [
            "NAME:LumpedPort1",
            "Faces:=", [int(face)],
            "DoDeembed:=", False,
            "RenormalizeAllTerminals:=", True,
            modes(),
            "ShowReporterFilter:=", False,
            "ReporterFilter:=", [True],
            "Impedance:=", "50ohm",
        ],
        "faces int no modes": [
            "NAME:LumpedPort1",
            "Faces:=", [int(face)],
            "DoDeembed:=", False,
            "RenormalizeAllTerminals:=", True,
            "ShowReporterFilter:=", False,
            "ReporterFilter:=", [True],
            "Impedance:=", "50ohm",
        ],
        "faces str no modes": [
            "NAME:LumpedPort1",
            "Faces:=", [face],
            "DoDeembed:=", False,
            "RenormalizeAllTerminals:=", True,
            "ShowReporterFilter:=", False,
            "ReporterFilter:=", [True],
            "Impedance:=", "50ohm",
        ],
        "faces int + modes + charmimp": [
            "NAME:LumpedPort1",
            "Faces:=", [int(face)],
            "DoDeembed:=", False,
            "RenormalizeAllTerminals:=", True,
            modes(),
            "ShowReporterFilter:=", False,
            "ReporterFilter:=", [True],
            "Impedance:=", "50ohm",
            "CharImp:=", "Zpi",
        ],
    }

    for label, payload in variants.items():
        try:
            module.AssignLumpedPort(payload)
            print(f"{label}: OK -> {list(module.GetExcitations())}")
            break
        except Exception as exc:
            print(f"{label}: FAIL {exc!r}")

    # maybe the sheet must be a standalone sheet (not merged into the model)
    print("\nobject list:")
    for name in ("Ground", "Strip", "PortSheet"):
        try:
            print(" ", name, "faces:", list(editor.GetFaceIDs(name)))
        except Exception as exc:
            print(" ", name, "err", exc)
finally:
    pythoncom.CoUninitialize()
