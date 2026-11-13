"""Throwaway: check the AEDT version and try PyAEDT's lumped port."""

import pythoncom
import win32com.client

pythoncom.CoInitialize()
try:
    app = win32com.client.Dispatch("Ansoft.ElectronicsDesktop")
    desktop = app.GetAppDesktop()
    print("AEDT version:", desktop.GetVersion())
    print("executable:", desktop.GetExeDir())
finally:
    pythoncom.CoUninitialize()

print("\n--- PyAEDT ---")
from ansys.aedt.core import Hfss

hfss = Hfss(
    project="PyAedtLumped",
    design="LumpedTest",
    solution_type="Modal",
    version="2022.1",
    non_graphical=False,
)

hfss.modeler.create_box([0, 0, 0], [20, 20, 1], "Ground", "copper")
hfss.modeler.create_box([5, 0, 1], [10, 20, 1], "Strip", "copper")

try:
    result = hfss.lumped_port(
        "Strip", "Ground", hfss.AxisDir.ZNeg, 50, "LumpedPort", True, False
    )
    print("PyAEDT lumped_port ->", result)
    print("excitations:", list(hfss.oboundary.GetExcitations()))
except Exception as exc:
    print("PyAEDT lumped_port failed:", repr(exc))
    try:
        print("excitations:", list(hfss.oboundary.GetExcitations()))
    except Exception as exc2:
        print("read failed:", repr(exc2))
