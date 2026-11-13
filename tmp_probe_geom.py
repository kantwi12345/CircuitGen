"""Throwaway: list the editor geometry-query methods and read a sheet bbox."""

import pythoncom
import win32com.client


def methods(obj, needle):
    ti = obj._oleobj_.GetTypeInfo(0)
    attr = ti.GetTypeAttr()
    cfuncs = attr[6] if isinstance(attr, tuple) else attr.cFuncs
    out = []
    for i in range(cfuncs):
        fd = ti.GetFuncDesc(i)
        memid = fd[0] if isinstance(fd, tuple) else fd.memid
        names = ti.GetNames(memid)
        if any(needle.lower() in n.lower() for n in names):
            out.append((names[0], names[1:]))
    return out


pythoncom.CoInitialize()
try:
    app = win32com.client.Dispatch("Ansoft.ElectronicsDesktop")
    desktop = app.GetAppDesktop()

    project = desktop.NewProject()
    project.InsertDesign("HFSS", "SheetGeom2", "DrivenModal", "")
    design = project.SetActiveDesign("SheetGeom2")
    editor = design.SetActiveEditor("3D Modeler")

    for name, args in methods(editor, "Vertex"):
        print("VERTEX:", name, args)
    for name, args in methods(editor, "Face"):
        print("FACE:", name, args)
    for name, args in methods(editor, "Point"):
        print("POINT:", name, args)
    for name, args in methods(editor, "Bound"):
        print("BOUND:", name, args)
finally:
    pythoncom.CoUninitialize()
