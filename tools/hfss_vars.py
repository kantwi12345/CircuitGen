"""
CircuitGen - HFSS design variables (Local Variables).

HFSS exposes no working COM call for creating design variables
(SetVariableValue / ChangeProperty on LocalVariableTab are both rejected),
so the Properties dialog (right-click the design -> "Design Properties...")
is driven through the GUI - which is exactly where the variables appear
in the table the user sees:

    Properties: <project> - <design>  ->  Local Variables tab

Adding a variable uses the "Add Property" modal:
    Name  : $f0
    Value : 2.4GHz      (number, variable or expression - units included)
    Type  : Variable
"""

import re
import time

import pythoncom
import win32com.client
import win32gui
from pywinauto import Desktop
from pywinauto.keyboard import send_keys

ADS_HFSS_TITLE = "Ansys Electronics Desktop"


def _uia():
    return Desktop(backend="uia")


def _win32():
    return Desktop(backend="win32")


def find_hfss_main(desk=None, timeout=30):
    """Find the HFSS main window (UIA, with a raw Win32 fallback)."""

    desk = desk or _uia()
    deadline = time.time() + timeout

    while time.time() < deadline:
        for window in desk.windows():
            try:
                if window.is_visible() and \
                        ADS_HFSS_TITLE in window.window_text():
                    return window
            except Exception:
                pass

        # raw Win32 lookup (UIA enumeration can miss the MFC frame)
        hits = []

        def callback(hwnd, _):
            if ADS_HFSS_TITLE in win32gui.GetWindowText(hwnd):
                hits.append(hwnd)

        win32gui.EnumWindows(callback, None)
        for hwnd in hits:
            try:
                window = desk.window(handle=hwnd)
                if window.exists():
                    return window
            except Exception:
                continue

        time.sleep(2.0)

    return None


def _dialog_windows(prefix):
    hits = []

    def callback(hwnd, _):
        if win32gui.GetWindowText(hwnd).startswith(prefix):
            hits.append(hwnd)

    win32gui.EnumWindows(callback, None)
    return hits


def close_properties_dialogs():
    """Close any Properties dialogs left open by a previous run."""

    for hwnd in _dialog_windows("Properties:"):
        try:
            win32gui.PostMessage(hwnd, win32gui.WM_CLOSE, 0, 0)
        except Exception:
            pass
    time.sleep(0.8)


def active_project_name(main):
    match = re.search(r"(Project\d+)", main.window_text())
    return match.group(1) if match else None


def find_design_tree_item(main, project, design_name="PatchAntenna"):
    """The design tree item under the given project."""

    items = []
    for control in main.descendants(control_type="TreeItem"):
        try:
            items.append(((control.window_text() or "").strip(), control))
        except Exception:
            pass

    for index, (name, control) in enumerate(items):
        if project and not name.startswith(project):
            continue
        for next_name, next_control in items[index + 1:index + 4]:
            if next_name.startswith(design_name):
                return next_control
        if project:
            break

    for name, control in items:
        if name.startswith(design_name):
            return control

    return None


def _popup_menu_items(desk=None):
    """Return the visible context-menu items (UIA backend)."""

    desk = desk or _uia()

    found = []
    for window in desk.windows():
        try:
            if not window.is_visible():
                continue
            if window.class_name() != "#32768" and \
                    "Popup" not in window.class_name():
                continue
            for control in window.descendants():
                try:
                    text = control.element_info.name or ""
                    if text:
                        found.append((text, control))
                except Exception:
                    pass
        except Exception:
            pass

    return found


def open_design_properties(main, desk=None, design_name="PatchAntenna"):
    """Open the design Properties dialog (win32 wrapper)."""

    desk = desk or _uia()

    close_properties_dialogs()
    send_keys("{ESC}")
    time.sleep(0.6)

    project = active_project_name(main)

    for attempt in range(5):
        item = find_design_tree_item(main, project, design_name)
        if item is None:
            return None

        try:
            main.set_focus()
            time.sleep(1.0)
            item.right_click_input()
        except Exception:
            pass
        time.sleep(1.5)

        # poll for the "Design Properties..." entry
        target = None
        for _ in range(10):
            for text, control in _popup_menu_items(desk):
                if text.startswith("Design Properties"):
                    target = control
                    break
            if target is not None:
                break
            time.sleep(0.8)

        if target is None:
            send_keys("{ESC}")
            time.sleep(1.0)
            continue

        try:
            target.click_input()
        except Exception:
            send_keys("{ESC}")
            time.sleep(1.0)
            continue

        # wait for the dialog
        for _ in range(15):
            time.sleep(1.0)
            for hwnd in _dialog_windows("Properties:"):
                title = win32gui.GetWindowText(hwnd)
                if project and project not in title:
                    continue
                return _win32().window(handle=hwnd)

        send_keys("{ESC}")
        time.sleep(1.0)

    return None


def _button(dialog, label):
    for control in dialog.descendants():
        try:
            if control.window_text().replace("&", "").strip() == label:
                return control
        except Exception:
            pass
    return None


def _add_property_modal():
    for window in _win32().windows():
        try:
            if window.is_visible() and window.window_text() == "Add Property":
                return window
        except Exception:
            pass
    return None


def _dismiss_warning():
    """Dismiss the 'must begin with a letter or an underscore' popup."""

    for window in _win32().windows():
        try:
            if not window.is_visible():
                continue
            title = window.window_text()
            if title in ("Ansys Electronics Desktop", "Error", "Warning"):
                for control in window.descendants():
                    if control.friendly_class_name() == "Button" and \
                            control.window_text().replace("&", "").strip() == "OK":
                        control.click()
                        time.sleep(0.8)
                        return True
        except Exception:
            pass
    return False


def add_variable(dialog, name, value):
    """Add one variable through Add... -> Add Property."""

    add_button = _button(dialog, "Add...")
    if add_button is None:
        return False

    add_button.click()
    time.sleep(2.0)

    modal = _add_property_modal()
    if modal is None:
        return False

    edits = []
    for control in modal.descendants():
        try:
            if control.friendly_class_name() == "Edit":
                edits.append(control)
        except Exception:
            pass

    if len(edits) < 2:
        return False

    edits.sort(key=lambda c: (c.rectangle().top, c.rectangle().left))
    name_edit = edits[0]
    value_edit = edits[-1]

    # make sure the type is a plain Variable
    for control in modal.descendants():
        try:
            if control.friendly_class_name() == "RadioButton" and \
                    control.window_text() == "Variable":
                control.click()
                break
        except Exception:
            pass

    # HFSS adds the '$' itself - the Name field takes the bare name
    bare_name = name[1:] if name.startswith("$") else name

    name_edit.set_focus()
    time.sleep(0.2)
    send_keys("^a{DELETE}")
    name_edit.type_keys(bare_name, with_spaces=False)
    time.sleep(0.2)

    value_edit.set_focus()
    time.sleep(0.2)
    send_keys("^a{DELETE}")
    value_edit.type_keys(str(value), with_spaces=False)
    time.sleep(0.3)

    ok = _button(modal, "OK")
    if ok is not None:
        ok.click()
    else:
        send_keys("{ENTER}")

    time.sleep(1.5)

    if _add_property_modal() is not None:
        # the dialog rejected the entry
        _dismiss_warning()
        return False

    _dismiss_warning()

    return True


def commit(dialog):
    """Apply and close the Properties dialog."""

    apply_button = _button(dialog, "Apply")
    if apply_button is not None:
        try:
            apply_button.click()
            time.sleep(1.5)
        except Exception:
            pass

    ok = _button(dialog, "OK")
    if ok is not None:
        try:
            ok.click()
        except Exception:
            send_keys("{ENTER}")
    time.sleep(1.5)


def _read_back(design_name="PatchAntenna"):
    """Read the variables HFSS reports for the design."""

    try:
        app = win32com.client.Dispatch("Ansoft.ElectronicsDesktop")
        desktop = app.GetAppDesktop()
        design = None
        for project in desktop.GetProjects():
            try:
                design = project.SetActiveDesign(design_name)
            except Exception:
                pass
        if design is None:
            return {}
        names = design.GetVariables()
        return {name: design.GetVariableValue(name) for name in names}
    except Exception:
        return {}


def set_design_variables(variables: dict, verify=True,
                         design_name="PatchAntenna"):
    """
    Populate the HFSS design's Local Variables from a {name: value} dict.
    """

    if not variables:
        return {"status": "no_variables"}

    pythoncom.CoInitialize()

    try:
        desk = _uia()
        main = find_hfss_main(desk)
        if main is None:
            return {"status": "hfss_not_running"}

        dialog = open_design_properties(main, desk, design_name)
        if dialog is None:
            return {"status": "properties_dialog_not_found"}

        added = []
        failed = []
        for name, value in variables.items():
            try:
                if add_variable(dialog, name, value):
                    added.append(name)
                else:
                    failed.append(name)
            except Exception as exc:
                failed.append(f"{name}: {exc}")

        commit(dialog)

        result = {"status": "variables_set", "added": added, "failed": failed}

        if verify:
            result["hfss_variables"] = _read_back(design_name)

        return result

    finally:
        pythoncom.CoUninitialize()


def set_design_variables_isolated(variables: dict, timeout=900,
                                  design_name="PatchAntenna"):
    """
    Run the GUI variable creation in a child process.

    The HFSS GUI automation can take the calling process down with it
    (access violation), so it is isolated here and the result is returned
    as JSON.
    """

    import json
    import subprocess
    import sys

    script = (
        "import json,sys;"
        "sys.path.insert(0, r'C:\\CircuitGen');"
        "from tools.hfss_vars import set_design_variables;"
        "print('@@RESULT@@' + json.dumps("
        "set_design_variables(json.loads(sys.argv[1]),"
        " design_name=sys.argv[2])))"
    )

    try:
        completed = subprocess.run(
            [sys.executable, "-c", script, json.dumps(variables), design_name],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {"status": "timeout"}

    output = completed.stdout or ""
    marker = "@@RESULT@@"

    if marker in output:
        payload = output.split(marker, 1)[1].strip()
        try:
            return json.loads(payload)
        except ValueError:
            pass

    return {
        "status": "failed",
        "returncode": completed.returncode,
        "stderr": (completed.stderr or "")[-500:],
    }


if __name__ == "__main__":
    import json
    import sys

    payload = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    design = sys.argv[2] if len(sys.argv) > 2 else "PatchAntenna"
    print(json.dumps(set_design_variables(payload, design_name=design)))
