"""Throwaway: isolated sheet vs touching sheet, and other excitation types."""

import pythoncom
import win32com.client


def build(design, touch):
    editor = design.SetActiveEditor("3D Modeler")
    editor.CreateBox(
        ["NAME:BoxParameters",
         "XPosition:=", "0mm", "YPosition:=", "0mm", "ZPosition:=", "0mm",
         "XSize:=", "20mm", "YSize:=", "20mm", "ZSize:=", "1mm"],
        ["NAME:Attributes", "Name:=", "Ground"],
    )
    if touch:
        z = "1mm"
    else:
        z = "5mm"
    editor.CreateRectangle(
        ["NAME:RectangleParameters",
         "IsCovered:=", True,
         "XStart:=", "8mm", "YStart:=", "0mm", "ZStart:=", z,
         "Width:=", "4mm", "Height:=", "1mm",
         "WhichAxis:=", "Y"],
        ["NAME:Attributes", "Name:=", "PortSheet"],
    )
    return editor


pythoncom.CoInitialize()
try:
    app = win32com.client.Dispatch("Ansoft.ElectronicsDesktop")
    desktop = app.GetAppDesktop()

    for label, touch in (("touching", True), ("floating", False)):
        project = desktop.NewProject()
        project.InsertDesign("HFSS", f"Probe_{label}", "DrivenModal", "")
        design = project.SetActiveDesign(f"Probe_{label}")
        editor = build(design, touch)
        module = design.GetModule("BoundarySetup")
        face = list(editor.GetFaceIDs("PortSheet"))[0]

        payload = [
            "NAME:LumpedPort1",
            "Faces:=", [int(face)],
            "DoDeembed:=", False,
            "RenormalizeAllTerminals:=", True,
            ["NAME:Modes",
             ["NAME:Mode1",
              "ModeNum:=", 1,
              "UseIntLine:=", True,
              ["NAME:IntLine",
               "Coordinate System:=", "Global",
               "Start:=", ["10mm", "0mm", "0mm"],
               "End:=", ["10mm", "0mm", "1mm"]],
              "AlignmentGroup:=", 0,
              "CharImp:=", "Zpi",
              "RenormImp:=", "50ohm"]],
            "ShowReporterFilter:=", False,
            "ReporterFilter:=", [True],
            "Impedance:=", "50ohm",
        ]

        try:
            module.AssignLumpedPort(payload)
            print(f"{label}: lumped OK -> {list(module.GetExcitations())}")
        except Exception as exc:
            print(f"{label}: lumped FAIL {exc!r}")

        # other excitation types for comparison
        for method, payload2 in (
            ("AssignTerminal", [
                "NAME:Term1",
                "Objects:=", ["Ground"],
                "RenormalizeAllTerminals:=", True,
                "DoDeembed:=", False,
                "Impedance:=", "50ohm",
            ]),
            ("AssignCircuitPort", [
                "NAME:CP1",
                "Objects:=", ["PortSheet"],
                "RenormalizeAllTerminals:=", True,
                "DoDeembed:=", False,
                "Impedance:=", "50ohm",
            ]),
        ):
            try:
                getattr(module, method)(payload2)
                print(f"{label}: {method} OK -> {list(module.GetExcitations())}")
                break
            except Exception as exc:
                print(f"{label}: {method} FAIL {exc!r}")
finally:
    pythoncom.CoUninitialize()
