"""Throwaway: does PyAEDT manage to create a lumped port on this AEDT?"""

import pythoncom
import win32com.client

pythoncom.CoInitialize()
try:
    app = win32com.client.Dispatch("Ansoft.ElectronicsDesktop")
    desktop = app.GetAppDesktop()

    project = desktop.NewProject()
    project.InsertDesign("HFSS", "PyAedtProbe", "DrivenModal", "")
    design = project.SetActiveDesign("PyAedtProbe")
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

    # PyAEDT style payload: no "Coordinate System" in the integration line
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
        print("pyaedt-style payload: OK ->", list(module.GetExcitations()))
    except Exception as exc:
        print("pyaedt-style payload: FAIL", repr(exc))

    # same but with "Objects:=" instead of "Faces:="
    payload_objects = list(payload)
    payload_objects[1] = "Objects:="
    payload_objects[2] = ["PortSheet"]

    try:
        module.AssignLumpedPort(payload_objects)
        print("pyaedt-style (objects): OK ->", list(module.GetExcitations()))
    except Exception as exc:
        print("pyaedt-style (objects): FAIL", repr(exc))
finally:
    pythoncom.CoUninitialize()
