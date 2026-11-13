"""Throwaway: explore the AEDT message manager so failures can be diagnosed."""

import pythoncom
import win32com.client

pythoncom.CoInitialize()
try:
    app = win32com.client.Dispatch("Ansoft.ElectronicsDesktop")
    desktop = app.GetAppDesktop()

    project = desktop.NewProject()
    project.InsertDesign("HFSS", "MsgProbe", "DrivenModal", "")
    design = project.SetActiveDesign("MsgProbe")
    editor = design.SetActiveEditor("3D Modeler")
    editor.CreateBox(
        ["NAME:BoxParameters",
         "XPosition:=", "0mm", "YPosition:=", "0mm", "ZPosition:=", "0mm",
         "XSize:=", "10mm", "YSize:=", "10mm", "ZSize:=", "1mm"],
        ["NAME:Attributes", "Name:=", "Box1"],
    )

    print("--- all severity-2 messages ---")
    for message in list(desktop.GetMessages("", "", 2)):
        print("  ", message)

    print("\n--- ClearMessages signature ---")
    ti = desktop._oleobj_.GetTypeInfo(0)
    attr = ti.GetTypeAttr()
    for i in range(attr[6]):
        fd = ti.GetFuncDesc(i)
        names = ti.GetNames(fd[0])
        if names[0] in ("ClearMessages", "GetMessages", "AddMessage"):
            print("  ", names[0], names[1:])

    try:
        desktop.ClearMessages()
        print("ClearMessages() ok")
    except Exception as exc:
        print("ClearMessages() failed:", repr(exc))

    module = design.GetModule("AnalysisSetup")

    try:
        module.InsertSetup("Setup1", [
            "NAME:Setup1",
            "Properties:=", [
                "NAME:Properties",
                "Enabled:=", True,
                "SetupType:=", "HFSSDriven",
                "Frequency:=", "2.4GHz",
                "MaxDeltaS:=", 0.1,
                "MaximumPasses:=", 10,
                "MinimumPasses:=", 1,
                "MinimumConvergedPasses:=", 1,
                "PercentRefinement:=", 30,
                "IsEnabled:=", True,
                "BasisOrder:=", 1,
                "DoLambdaRefine:=", True,
                "DoMaterialLambda:=", True,
                "SetLambdaTarget:=", False,
                "Target:=", 0.3333,
                "UseMaxTetIncrease:=", False,
                "PortAccuracy:=", 2,
                "UseABCOnPort:=", False,
                "SetPortMinMaxTri:=", False,
                "MinTrianglesForPort:=", 100,
            ],
        ])
        print("InsertSetup OK ->", list(module.GetSetups() or []))
    except Exception as exc:
        print("InsertSetup FAIL:", repr(exc))

    print("\n--- all severity-2 messages after ---")
    for message in list(desktop.GetMessages("", "", 2)):
        print("  ", message)

    print("\n--- project/design filtered ---")
    for args in ((project, design), (project.GetName(), design.GetName())):
        try:
            print(args, "->", list(desktop.GetMessages(*args, 2)))
        except Exception as exc:
            print(args, "failed", repr(exc))
finally:
    pythoncom.CoUninitialize()
