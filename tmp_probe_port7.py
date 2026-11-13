"""Throwaway: bisect which lumped-port property HFSS rejects."""

import itertools

import pythoncom
import win32com.client

pythoncom.CoInitialize()
try:
    app = win32com.client.Dispatch("Ansoft.ElectronicsDesktop")
    desktop = app.GetAppDesktop()

    project = desktop.NewProject()
    project.InsertDesign("HFSS", "Bisect", "DrivenModal", "")
    design = project.SetActiveDesign("Bisect")
    editor = design.SetActiveEditor("3D Modeler")

    editor.CreateBox(
        ["NAME:BoxParameters",
         "XPosition:=", "0mm", "YPosition:=", "0mm", "ZPosition:=", "0mm",
         "XSize:=", "20mm", "YSize:=", "20mm", "ZSize:=", "1mm"],
        ["NAME:Attributes", "Name:=", "Ground"],
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

    extras = {
        "renorm": ["RenormalizeAllTerminals:=", True],
        "dedeembed": ["DoDeembed:=", False],
        "reporter": ["ShowReporterFilter:=", False, "ReporterFilter:=", [True]],
        "modes": [
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
        ],
    }

    names = list(extras)

    for size in range(len(names) + 1):
        for combo in itertools.combinations(names, size):
            payload = ["NAME:LumpedPort1", "Faces:=", [int(face)]]
            for key in combo:
                payload.extend(extras[key])
            payload.append("Impedance:=")
            payload.append("50ohm")

            try:
                module.AssignLumpedPort(payload)
                print(f"OK   with {combo}")
                print("     excitations:", list(module.GetExcitations()))
                raise SystemExit(0)
            except SystemExit:
                raise
            except Exception as exc:
                print(f"FAIL with {combo}: {exc.args[2][4] if exc.args[2] else exc}")
finally:
    pythoncom.CoUninitialize()
