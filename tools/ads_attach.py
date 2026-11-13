"""
CircuitGen - ADS GUI automation helper.

ADS 2023 exposes no COM/CLI automation on Windows (verified), so the
workspace is attached by driving the ADS GUI with pywinauto (UIA):

    File > Open > Workspace...   -> type the folder -> "Select Folder"
    File > New Schematic (toolbar) -> library + cell name -> Create

Usage:
    python tools/ads_attach.py --workspace C:\\ADS_Projects\\LNA_wrk --cell lna
"""

import os
import time

from pywinauto import Desktop, mouse
from pywinauto.keyboard import send_keys

ADS_EXE = r"C:\Program Files\Keysight\ADS2023_Update1\bin\ads.exe"


def _ads_windows(desk=None):
    desk = desk or Desktop(backend="uia")
    found = []
    for window in desk.windows():
        try:
            if window.class_name() == "MainWindowWidgetC" and \
                    "Advanced Design System" in window.window_text():
                found.append(window)
        except Exception:
            pass
    return found


def _uia():
    """UIA desktop helper."""

    return Desktop(backend="uia")


def _ads_window(desk=None, timeout=60):
    """Return the ADS main window, launching ADS if needed."""

    desk = desk or Desktop(backend="uia")
    deadline = time.time() + timeout

    while time.time() < deadline:
        windows = _ads_windows(desk)
        if windows:
            # newest instance last (highest pid)
            return sorted(windows, key=lambda w: w.process_id())[-1]
        time.sleep(2)

    return None


def launch_ads(timeout=180):
    import subprocess

    subprocess.Popen([ADS_EXE])

    desk = Desktop(backend="uia")
    deadline = time.time() + timeout

    while time.time() < deadline:
        # ADS can show a product/bundle selection dialog on first start
        for window in desk.windows():
            try:
                if window.is_visible() and \
                        "Product Selection" in window.window_text():
                    window.set_focus()
                    time.sleep(0.5)
                    send_keys("{ENTER}")
                    break
            except Exception:
                pass

        windows = _ads_windows(desk)
        if windows:
            return sorted(windows, key=lambda w: w.process_id())[-1]

        time.sleep(2)

    return None


def _find_menu_item(win, label, timeout=10):
    """Find a menu item in the main window or in any open popup.

    Prefers the most recently created visible match - Qt keeps stale
    elements around after a menu closes, and clicking those does nothing.
    """

    desk = Desktop(backend="uia")
    deadline = time.time() + timeout

    while time.time() < deadline:
        matches = []

        for item in win.descendants(control_type="MenuItem"):
            try:
                if item.window_text() == label and item.is_visible():
                    rect = item.rectangle()
                    if rect.width() > 0 and rect.height() > 0:
                        matches.append(item)
            except Exception:
                pass

        if not matches:
            for window in desk.windows():
                try:
                    if not window.is_visible():
                        continue
                    for item in window.descendants(control_type="MenuItem"):
                        if item.window_text() == label and item.is_visible():
                            rect = item.rectangle()
                            if rect.width() > 0 and rect.height() > 0:
                                matches.append(item)
                except Exception:
                    pass

        if matches:
            return matches[-1]

        time.sleep(0.4)

    return None


def _click_menu(win, labels, attempts=4):
    """Click through a menu path, e.g. ('File', 'Open', 'Workspace...')."""

    last_error = None

    for _ in range(attempts):
        try:
            win.set_focus()
            time.sleep(1.0)

            for index, label in enumerate(labels):
                target = None
                deadline = time.time() + 12

                while time.time() < deadline and target is None:
                    target = _find_menu_item(win, label, timeout=0.6)
                    if target is None and index > 0:
                        # Qt submenus open on hover - hover the parent
                        parent = _find_menu_item(win, labels[index - 1],
                                                 timeout=0.5)
                        if parent is not None:
                            try:
                                rect = parent.rectangle()
                                mouse.move(coords=(rect.mid_point().x,
                                                   rect.mid_point().y))
                            except Exception:
                                pass
                    time.sleep(0.4)

                if target is None:
                    raise RuntimeError(f"menu item not found: {label}")

                try:
                    target.click_input()
                except Exception:
                    pass
                time.sleep(1.6)

            return

        except RuntimeError as exc:
            last_error = exc
            send_keys("{ESC}")
            time.sleep(1.5)

    raise last_error


def open_workspace(workspace_dir, timeout=120, desk=None):
    """Attach a workspace in ADS via File > Open > Workspace....

    Returns (result, window) - the window is reused for follow-up steps.
    """

    if not os.path.isdir(workspace_dir):
        return {
            "status": "workspace_not_found",
            "workspace": workspace_dir,
        }, None

    desk = desk or Desktop(backend="uia")
    win = _ads_window(desk)
    if win is None:
        win = launch_ads()
    if win is None:
        return {"status": "ads_not_running"}, None

    folder_edit = None
    select_button = None

    for attempt in range(3):
        try:
            win.set_focus()
            # the workspace browser lives in the File View tab
            for tab in win.descendants(control_type="TabItem"):
                if (tab.element_info.name or "") == "File View":
                    tab.click_input()
                    time.sleep(1.0)
                    break
            time.sleep(0.5)
        except Exception:
            pass

        _click_menu(win, ("File", "Open", "Workspace..."))
        time.sleep(2.5)

        folder_edit = None
        select_button = None
        for ctl in win.descendants():
            try:
                info = ctl.element_info
                if info.control_type == "Edit" and \
                        info.class_name in ("Edit", "QLineEdit"):
                    if folder_edit is None or \
                            (info.name or "").lower().startswith("folder"):
                        folder_edit = ctl
                if info.control_type == "Button" and \
                        (info.name or "").lower().startswith("select folder"):
                    select_button = ctl
            except Exception:
                pass

        if folder_edit is not None:
            break

        send_keys("{ESC}")
        time.sleep(1.5)

    if folder_edit is None:
        return {"status": "folder_field_not_found"}, win

    folder_edit.set_focus()
    time.sleep(0.3)
    send_keys("^a{DELETE}")
    folder_edit.type_keys(workspace_dir, with_spaces=True, with_tabs=False)
    time.sleep(0.5)

    if select_button is not None:
        select_button.click_input()
    else:
        send_keys("{ENTER}")

    # wait for ADS to load the workspace
    deadline = time.time() + timeout
    loaded = False
    while time.time() < deadline:
        time.sleep(3)
        try:
            for item in win.descendants():
                name = item.element_info.name or ""
                if os.path.basename(workspace_dir) in name:
                    loaded = True
                    break
        except Exception:
            pass
        if loaded:
            break
        for marker in ("netlist.log", "search_history.log", "readegs.log"):
            if os.path.exists(os.path.join(workspace_dir, marker)):
                loaded = True
                break
        if loaded:
            break

    return {
        "status": "workspace_opened" if loaded else "workspace_open_unverified",
        "workspace": workspace_dir,
        "cell": None,
    }, win


def cell_exists(workspace_dir, library_name, cell_name) -> bool:
    """True when the cell is already present in the workspace library."""

    path = os.path.join(
        workspace_dir, library_name, cell_name, "schematic", "sch.oa")
    return os.path.exists(path)


def _dismiss_dialogs():
    """Close any leftover modal (New Schematic / Confirm / Error)."""

    for window in _uia().windows():
        try:
            if not window.is_visible():
                continue
            title = window.window_text()
            if title in ("New Schematic", "Confirm New Schematic",
                         "New Design Error"):
                for control in window.descendants(control_type="Button"):
                    name = (control.element_info.name or "").strip()
                    if name in ("OK", "Cancel", "No", "Close"):
                        control.click_input()
                        time.sleep(1.0)
                        break
        except Exception:
            pass


def _library_cell_item(win, cell_name):
    """Find a cell in the ADS Library View tree."""

    for tab in win.descendants(control_type="TabItem"):
        try:
            if (tab.element_info.name or "") == "Library View":
                tab.click_input()
                time.sleep(1.5)
                break
        except Exception:
            pass

    for item in win.descendants(control_type="TreeItem"):
        try:
            name = (item.window_text() or "").strip()
            if name == cell_name or name.startswith(f"{cell_name} "):
                return item
        except Exception:
            pass

    return None


def open_cell(win, cell_name, timeout=40):
    """Open an existing cell from the library (no creation prompt)."""

    item = _library_cell_item(win, cell_name)
    if item is None:
        return {"status": "cell_not_found"}

    try:
        item.double_click_input()
    except Exception:
        return {"status": "cell_open_failed"}

    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(2)
        for window in _uia().windows():
            try:
                if window.is_visible() and cell_name in window.window_text():
                    return {
                        "status": "cell_opened",
                        "title": window.window_text(),
                    }
            except Exception:
                pass

    return {"status": "cell_open_timeout"}


def create_schematic(workspace_dir, cell_name, timeout=90, win=None, desk=None):
    """Create a schematic cell via the toolbar New Schematic button."""

    desk = desk or Desktop(backend="uia")
    win = win or _ads_window(desk)
    if win is None:
        return {"status": "ads_not_running"}

    win.set_focus()
    time.sleep(0.8)

    button = None
    for ctl in win.descendants():
        try:
            if (ctl.element_info.name or "") == "New Schematic":
                button = ctl
                break
        except Exception:
            pass

    if button is None:
        try:
            _click_menu(win, ("File", "New", "Schematic..."))
        except Exception as exc:
            return {"status": "new_schematic_button_not_found",
                    "error": str(exc)}
    else:
        button.click_input()
    time.sleep(3)

    # The New Schematic dialog has a name edit and a library selector.
    name_edit = None
    for ctl in win.descendants():
        try:
            info = ctl.element_info
            if info.control_type == "Edit" and \
                    info.class_name in ("Edit", "QLineEdit"):
                if name_edit is None:
                    name_edit = ctl
        except Exception:
            pass

    if name_edit is not None:
        name_edit.set_focus()
        time.sleep(0.3)
        send_keys("^a{DELETE}")
        name_edit.type_keys(cell_name, with_spaces=False, with_tabs=False)
        time.sleep(0.5)
        send_keys("{ENTER}")
        time.sleep(3)

    return {
        "status": "schematic_requested",
        "workspace": workspace_dir,
        "cell": cell_name,
    }


def play_macro(macro_path, timeout=240, win=None, desk=None):
    """Play an AEL macro inside ADS via Tools > Playback Macro...."""

    desk = desk or Desktop(backend="uia")
    win = win or _ads_window(desk)
    if win is None:
        win = launch_ads()
    if win is None:
        return {"status": "ads_not_running"}

    if not os.path.exists(macro_path):
        return {"status": "macro_not_found", "macro": macro_path}

    _click_menu(win, ("Tools", "Playback Macro..."))
    time.sleep(3)

    name_edit = None
    for window in desk.windows():
        try:
            if not window.is_visible() or window.process_id() != win.process_id():
                continue
            for ctl in window.descendants(control_type="Edit"):
                try:
                    info = ctl.element_info
                    if info.class_name == "Edit" and \
                            (info.name or "").lower().startswith("file name"):
                        name_edit = ctl
                except Exception:
                    pass
        except Exception:
            pass

    if name_edit is None:
        return {"status": "macro_file_dialog_not_found"}

    name_edit.set_focus()
    time.sleep(0.3)
    send_keys("^a{DELETE}")
    name_edit.type_keys(macro_path, with_spaces=True)
    time.sleep(0.5)
    send_keys("{ENTER}")

    # give ADS time to run the macro
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(5)
        break

    return {
        "status": "macro_played",
        "macro": macro_path,
    }


def attach(workspace_dir, cell_name=None, library_name=None):
    """Open the workspace in ADS and optionally open/create the schematic cell."""

    result, win = open_workspace(workspace_dir)

    if cell_name and win is not None and result.get("status") in (
            "workspace_opened", "workspace_open_unverified"):
        _dismiss_dialogs()

        # an existing cell cannot be overwritten - open it instead
        if library_name and cell_exists(workspace_dir, library_name, cell_name):
            opened = open_cell(win, cell_name)
            result = {
                "status": opened.get("status", "cell_exists"),
                "workspace": workspace_dir,
                "cell": cell_name,
                "note": "cell already exists - opened instead of recreated",
            }
        else:
            result = create_schematic(workspace_dir, cell_name, win=win)

    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Attach a CircuitGen ADS workspace in ADS 2023")
    parser.add_argument("--workspace", required=True,
                        help="workspace directory, e.g. C:\\ADS_Projects\\LNA_wrk")
    parser.add_argument("--cell", default=None,
                        help="schematic cell name to create (no spaces)")

    args = parser.parse_args()
    print(attach(args.workspace, args.cell))
