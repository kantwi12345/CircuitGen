"""Throwaway: read the port sheet geometry and assign a correct lumped port."""

import pythoncom
import win32com.client


def last_error(desktop):
    try:
        messages = list(desktop.GetMessages("", "", 2))[-1]
        return messages
    except Exception as exc:
        return f"<no message: {exc!r}>"


pythoncom.CoInitialize()
try:
    app = win32com.client.Dispatch("Ansoft.ElectronicsDesktop")
    desktop = app.GetAppDesktop()

    project = desktop.NewProject()
    project.InsertDesign("HFSS", "SheetGeom", "DrivenModal", "")
    design = project.SetActiveDesign("SheetGeom")
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

    face = list(editor.GetFaceIDsOfSheet("PortSheet"))[0]
    print("sheet face id:", face)

    vertices = list(editor.GetVertexIDsOfFace(face))
    print("vertices:", vertices)
    for vertex in vertices:
        print("  ", vertex, list(editor.GetVertexPosition(vertex)))

    try:
        print("face center:", list(editor.GetFaceCenter(face)))
    except Exception as exc:
        print("GetFaceCenter failed:", repr(exc))

    # derive the integration line from the sheet extents
    positions = [list(editor.GetVertexPosition(v)) for v in vertices]
    xs = [p[0] for p in positions]
    ys = [p[1] for p in positions]
    zs = [p[2] for p in positions]

    x = (min(xs) + max(xs)) / 2.0
    y = (min(ys) + max(ys)) / 2.0
    z0, z1 = min(zs), max(zs)

    print(f"integration line: ({x}, {y}, {z0}) -> ({x}, {y}, {z1})")

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
        print("AssignLumpedPort OK ->", list(module.GetExcitations()))
    except Exception as exc:
        print("AssignLumpedPort FAIL", repr(exc))
        print("AEDT says:", last_error(desktop))
finally:
    pythoncom.CoUninitialize()
