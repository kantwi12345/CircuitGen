"""Throwaway: find the InsertSetup payload HFSS 2022.1 accepts."""

import pythoncom
import win32com.client


def last_error(desktop):
    try:
        return list(desktop.GetMessages("", "", 2))[-1]
    except Exception as exc:
        return f"<none: {exc!r}>"


pythoncom.CoInitialize()
try:
    app = win32com.client.Dispatch("Ansoft.ElectronicsDesktop")
    desktop = app.GetAppDesktop()

    project = desktop.NewProject()
    project.InsertDesign("HFSS", "SetupProbe", "DrivenModal", "")
    design = project.SetActiveDesign("SetupProbe")

    module = design.GetModule("AnalysisSetup")

    variants = {
        "minimal": [
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
        ],
        "with mesh": [
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
                "MeshOptions:=", [
                    "NAME:MeshOptions",
                    "MeshType:=", "Auto",
                    "MaxDeltaS:=", 0.1,
                    "MaxPasses:=", 10,
                ],
            ],
        ],
        "solver block": [
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
            "NAME:PreSolveSetup",
        ],
    }

    for label, payload in variants.items():
        try:
            desktop.ClearMessages()
        except Exception:
            pass
        try:
            module.InsertSetup("Setup1", payload)
            print(f"{label}: OK -> setups {list(module.GetSetups() or [])}")
            break
        except Exception as exc:
            print(f"{label}: FAIL")
            print("   AEDT says:", last_error(desktop))
finally:
    pythoncom.CoUninitialize()
