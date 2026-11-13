"""Throwaway: build the integration line from real sheet geometry."""

import pythoncom
import win32com.client


def last_error(desktop):
    try:
        return list(desktop.GetMessages("", "", 2))[-1]
    except Exception as exc:
        return f"<no message: {exc!r}>"


def sheet_geometry(editor, sheet_name):
    face = list(editor.GetFaceIDsOfSheet(sheet_name))[0]
    vertices = list(editor.GetVertexIDsFromFace(face))
    positions = [list(editor.GetVertexPosition(v)) for v in vertices]
    return face, positions


pythoncom.CoInitialize()
try:
    app = win32com.client.Dispatch("Ansoft.ElectronicsDesktop")
    desktop = app.GetAppDesktop()

    for label, sheet_z, touch in (("on ground", "0mm", True), ("floating", "5mm", False)):
        project = desktop.NewProject()
        project.InsertDesign("HFSS", f"Sheet_{label.replace(' ', '_')}", "DrivenModal", "")
        design = project.SetActiveDesign(f"Sheet_{label.replace(' ', '_')}")
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
             "XStart:=", "8mm", "YStart:=", "0mm", "ZStart:=", sheet_z,
             "Width:=", "4mm", "Height:=", "1mm",
             "WhichAxis:=", "Y"],
            ["NAME:Attributes", "Name:=", "PortSheet"],
        )

        face, positions = sheet_geometry(editor, "PortSheet")
        positions = [[float(v) for v in p] for p in positions]
        xs = [p[0] for p in positions]
        ys = [p[1] for p in positions]
        zs = [p[2] for p in positions]

        print(f"\n=== {label} ===")
        print("face:", face, "vertices:", positions)
        print("extent x", min(xs), max(xs), " y", min(ys), max(ys), " z", min(zs), max(zs))

        x = (min(xs) + max(xs)) / 2.0
        y = (min(ys) + max(ys)) / 2.0
        z0, z1 = min(zs), max(zs)

        module = design.GetModule("BoundarySetup")

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
               "Start:=", [f"{x:g}mm", f"{y:g}mm", f"{z0:g}mm"],
               "End:=", [f"{x:g}mm", f"{y:g}mm", f"{z1:g}mm"]],
              "AlignmentGroup:=", 0,
              "CharImp:=", "Zpi",
              "RenormImp:=", "50ohm"]],
            "ShowReporterFilter:=", False,
            "ReporterFilter:=", [True],
            "Impedance:=", "50ohm",
        ]

        try:
            module.AssignLumpedPort(payload)
            print("OK ->", list(module.GetExcitations()))
        except Exception as exc:
            print("FAIL", repr(exc))
            print("AEDT says:", last_error(desktop))
finally:
    pythoncom.CoUninitialize()
