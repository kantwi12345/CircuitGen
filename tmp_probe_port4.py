"""Throwaway: validate the HFSS 2022 lumped-port payload."""

import pythoncom
import win32com.client

pythoncom.CoInitialize()
try:
    app = win32com.client.Dispatch("Ansoft.ElectronicsDesktop")
    desktop = app.GetAppDesktop()

    project = desktop.NewProject()
    project.InsertDesign("HFSS", "PortProbe4", "DrivenModal", "")
    design = project.SetActiveDesign("PortProbe4")
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

    print("GetFaceIDs:", list(editor.GetFaceIDs("PortSheet")))
    print("GetFaceIDsOfSheet:", list(editor.GetFaceIDsOfSheet("PortSheet")))

    face_ids = list(editor.GetFaceIDs("PortSheet"))
    module = design.GetModule("BoundarySetup")

    payload = [
        "NAME:LumpedPort1",
        "Faces:=", face_ids,
        "DoDeembed:=", False,
        "RenormalizeAllTerminals:=", True,
        ["NAME:Modes",
         ["NAME:Mode1",
          "ModeNum:=", 1,
          "UseIntLine:=", True,
          ["NAME:IntLine",
           "Coordinate System:=", "Global",
           "Start:=", ["10mm", "0mm", "0mm"],
           "End:=", ["10mm", "0mm", "1mm"],
           ],
          "AlignmentGroup:=", 0,
          "CharImp:=", "Zpi",
          "RenormImp:=", "50ohm"]],
        "ShowReporterFilter:=", False,
        "ReporterFilter:=", [True],
        "Impedance:=", "50ohm",
    ]

    try:
        module.AssignLumpedPort(payload)
        print("modern payload: OK")
        print("excitations:", list(module.GetExcitations()))
    except Exception as exc:
        print("modern payload: FAIL", repr(exc))
finally:
    pythoncom.CoUninitialize()
