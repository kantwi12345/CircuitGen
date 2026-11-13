"""
CircuitGen - antenna geometry validation.

Builds each antenna in HFSS at several frequencies and checks the geometry
that HFSS actually created against the intended parametric layout.

    python validate_antennas.py
"""

import sys

import pythoncom
import win32com.client

sys.path.insert(0, r"C:\CircuitGen")

from tools.antenna_calcs import (
    patch_layout,
    monopole_layout,
    dipole_layout,
)
from tools.patch_builder import create_patch_antenna
from tools.hfss_com import create_monopole_antenna, create_dipole_antenna

FREQUENCIES = [0.9, 1.8, 2.4, 3.6, 5.2, 10.0]


def last_design(design_name):
    """Return the most recently created design with the given name."""

    pythoncom.CoInitialize()

    app = win32com.client.Dispatch("Ansoft.ElectronicsDesktop")
    desktop = app.GetAppDesktop()

    design = None
    for project in desktop.GetProjects():
        try:
            design = project.SetActiveDesign(design_name)
        except Exception:
            pass

    return design


def prop(editor, object_name, name):
    try:
        return editor.GetPropertyValue(
            "Geometry3DCmdTab", object_name, name)
    except Exception:
        return None


def num(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace("mm", "").replace(" ", "")
    try:
        return float(text)
    except ValueError:
        return None


def to_floats(text):
    if not text:
        return []
    values = []
    for part in str(text).replace(",", " ").split():
        try:
            values.append(float(part))
        except ValueError:
            continue
    return values


def check_close(label, actual, expected, tolerance=0.05, failures=None):
    actual = num(actual)
    if actual is None:
        failures.append(f"{label}: not readable from HFSS")
        return
    if abs(actual - expected) > tolerance:
        failures.append(
            f"{label}: HFSS {actual} != expected {expected} "
            f"(delta {actual - expected:+.3f} mm)"
        )


def validate_patch(freq):
    layout = patch_layout(freq, er=4.4, h_mm=1.6)
    create_patch_antenna(frequency_ghz=freq, er=4.4, thickness_mm=1.6)

    editor = last_design("PatchAntenna").SetActiveEditor("3D Modeler")
    failures = list(layout["checks"])

    sub = to_floats(prop(editor, "FR4_Substrate:CreateBox:1", "Position"))
    check_close("substrate X", sub[0] if sub else None, 0, failures=failures)
    check_close("substrate Y", sub[1] if len(sub) > 1 else None, 0, failures=failures)
    check_close("substrate Z", sub[2] if len(sub) > 2 else None, 0, failures=failures)
    check_close("substrate XSize", prop(editor, "FR4_Substrate:CreateBox:1", "XSize"),
                layout["board_x_mm"], failures=failures)
    check_close("substrate YSize", prop(editor, "FR4_Substrate:CreateBox:1", "YSize"),
                layout["board_y_mm"], failures=failures)
    check_close("substrate ZSize", prop(editor, "FR4_Substrate:CreateBox:1", "ZSize"),
                layout["thickness_mm"], failures=failures)

    patch = to_floats(prop(editor, "Patch:CreateRectangle:1", "Position"))
    check_close("patch X", patch[0] if patch else None, layout["patch_x_mm"], failures=failures)
    check_close("patch Y", patch[1] if len(patch) > 1 else None, layout["patch_y_mm"], failures=failures)
    check_close("patch Z", patch[2] if len(patch) > 2 else None, layout["thickness_mm"], failures=failures)
    check_close("patch XSize", prop(editor, "Patch:CreateRectangle:1", "XSize"),
                layout["patch_width_mm"], failures=failures)
    check_close("patch YSize", prop(editor, "Patch:CreateRectangle:1", "YSize"),
                layout["patch_length_mm"], failures=failures)

    feed = to_floats(prop(editor, "FeedLine:CreateRectangle:1", "Position"))
    check_close("feed X", feed[0] if feed else None, layout["feed_x_mm"], failures=failures)
    check_close("feed Y", feed[1] if len(feed) > 1 else None, 0, failures=failures)
    check_close("feed Z", feed[2] if len(feed) > 2 else None, layout["thickness_mm"], failures=failures)
    check_close("feed XSize", prop(editor, "FeedLine:CreateRectangle:1", "XSize"),
                layout["feed_width_mm"], failures=failures)
    check_close("feed YSize", prop(editor, "FeedLine:CreateRectangle:1", "YSize"),
                layout["feed_length_mm"], failures=failures)

    port = to_floats(prop(editor, "PortSheet:CreateRectangle:1", "Position"))
    check_close("port X", port[0] if port else None, layout["port_x_mm"], failures=failures)
    check_close("port Y", port[1] if len(port) > 1 else None, 0, failures=failures)
    check_close("port Z", port[2] if len(port) > 2 else None, 0, failures=failures)
    check_close("port XSize", prop(editor, "PortSheet:CreateRectangle:1", "XSize"),
                layout["feed_width_mm"], failures=failures)
    check_close("port ZSize", prop(editor, "PortSheet:CreateRectangle:1", "ZSize"),
                layout["thickness_mm"], failures=failures)

    air = to_floats(prop(editor, "AirBox:CreateBox:1", "Position"))
    check_close("air X", air[0] if air else None, layout["air_x_mm"], failures=failures)
    check_close("air Y", air[1] if len(air) > 1 else None, layout["air_y_mm"], failures=failures)
    check_close("air Z", air[2] if len(air) > 2 else None, layout["air_z_mm"], failures=failures)
    check_close("air XSize", prop(editor, "AirBox:CreateBox:1", "XSize"),
                layout["air_size_x_mm"], failures=failures)
    check_close("air YSize", prop(editor, "AirBox:CreateBox:1", "YSize"),
                layout["air_size_y_mm"], failures=failures)
    check_close("air ZSize", prop(editor, "AirBox:CreateBox:1", "ZSize"),
                layout["air_size_z_mm"], failures=failures)

    if patch and feed:
        feed_end = feed[1] + layout["feed_length_mm"]
        if abs(feed_end - patch[1]) > 0.05:
            failures.append(
                f"feed ends at Y={feed_end:.3f} but patch starts at "
                f"Y={patch[1]:.3f} - not connected")
        if abs((feed[0] + layout["feed_width_mm"] / 2.0)
               - (patch[0] + layout["patch_width_mm"] / 2.0)) > 0.05:
            failures.append("feed line is not centred on the patch")

    if port and feed and abs(port[0] - feed[0]) > 0.05:
        failures.append("port sheet is not aligned with the feed line")

    lam0 = layout["lambda0_mm"]
    if air:
        if air[2] + layout["air_size_z_mm"] - layout["thickness_mm"] < lam0 / 4.0 - 0.05:
            failures.append("air box is less than lambda/4 above the radiator")

    return layout, failures


def validate_monopole(freq):
    layout = monopole_layout(freq)
    create_monopole_antenna(frequency_ghz=freq)

    editor = last_design("MonopoleAntenna").SetActiveEditor("3D Modeler")
    failures = list(layout["checks"])

    check_close("radiator height", prop(editor, "Monopole:CreateCylinder:1", "Height"),
                layout["monopole_length_mm"], failures=failures)
    check_close("radiator radius", prop(editor, "Monopole:CreateCylinder:1", "Radius"),
                layout["monopole_radius_mm"], failures=failures)

    radiator = to_floats(
        prop(editor, "Monopole:CreateCylinder:1", "Center Position"))
    check_close("radiator X", radiator[0] if radiator else None, 0, failures=failures)
    check_close("radiator Y", radiator[1] if len(radiator) > 1 else None, 0, failures=failures)
    check_close("radiator Z", radiator[2] if len(radiator) > 2 else None, 1.0,
                failures=failures)

    ground = to_floats(prop(editor, "GroundPlane:CreateRectangle:1", "Position"))
    check_close("ground X", ground[0] if ground else None,
                -layout["ground_half_mm"], failures=failures)
    check_close("ground Y", ground[1] if len(ground) > 1 else None,
                -layout["ground_half_mm"], failures=failures)
    check_close("ground XSize", prop(editor, "GroundPlane:CreateRectangle:1", "XSize"),
                2 * layout["ground_half_mm"], failures=failures)
    check_close("ground YSize", prop(editor, "GroundPlane:CreateRectangle:1", "YSize"),
                2 * layout["ground_half_mm"], failures=failures)

    port = to_floats(prop(editor, "PortSheet:CreateRectangle:1", "Position"))
    check_close("port X", port[0] if port else None,
                -layout["monopole_radius_mm"], failures=failures)
    check_close("port XSize", prop(editor, "PortSheet:CreateRectangle:1", "XSize"),
                2 * layout["monopole_radius_mm"], failures=failures)

    air = to_floats(prop(editor, "AirBox:CreateBox:1", "Position"))
    check_close("air X", air[0] if air else None, layout["air_x_mm"], failures=failures)
    check_close("air XSize", prop(editor, "AirBox:CreateBox:1", "XSize"),
                layout["air_size_xy_mm"], failures=failures)
    check_close("air ZSize", prop(editor, "AirBox:CreateBox:1", "ZSize"),
                layout["air_size_z_mm"], failures=failures)

    if air:
        clearance = air[2] + layout["air_size_z_mm"] - (1.0 + layout["monopole_length_mm"])
        if clearance < layout["lambda0_mm"] / 4.0 - 0.05:
            failures.append(
                f"air box is only {clearance:.1f} mm above the radiator "
                f"(need lambda/4 = {layout['lambda0_mm']/4.0:.1f} mm)")

    return layout, failures


def validate_dipole(freq):
    layout = dipole_layout(freq)
    create_dipole_antenna(frequency_ghz=freq)

    editor = last_design("DipoleAntenna").SetActiveEditor("3D Modeler")
    failures = list(layout["checks"])

    check_close("dipole height", prop(editor, "Dipole:CreateCylinder:1", "Height"),
                layout["dipole_length_mm"], failures=failures)
    check_close("dipole radius", prop(editor, "Dipole:CreateCylinder:1", "Radius"),
                layout["dipole_radius_mm"], failures=failures)

    dipole = to_floats(
        prop(editor, "Dipole:CreateCylinder:1", "Center Position"))
    check_close("dipole X", dipole[0] if dipole else None, 0, failures=failures)
    check_close("dipole Y", dipole[1] if len(dipole) > 1 else None, 0, failures=failures)
    check_close("dipole Z", dipole[2] if len(dipole) > 2 else None,
                -layout["dipole_length_mm"] / 2.0, failures=failures)

    check_close("gap height", prop(editor, "Gap:CreateCylinder:1", "Height"),
                layout["gap_length_mm"], failures=failures)
    check_close("gap radius", prop(editor, "Gap:CreateCylinder:1", "Radius"),
                layout["gap_radius_mm"], failures=failures)

    gap = to_floats(prop(editor, "Gap:CreateCylinder:1", "Center Position"))
    check_close("gap Z", gap[2] if len(gap) > 2 else None,
                -layout["gap_length_mm"] / 2.0, failures=failures)

    port = to_floats(prop(editor, "PortSheet:CreateRectangle:1", "Position"))
    check_close("port X", port[0] if port else None,
                -layout["gap_radius_mm"], failures=failures)
    check_close("port Z", port[2] if len(port) > 2 else None,
                -layout["gap_length_mm"] / 2.0, failures=failures)
    check_close("port XSize", prop(editor, "PortSheet:CreateRectangle:1", "XSize"),
                2 * layout["gap_radius_mm"], failures=failures)
    check_close("port ZSize", prop(editor, "PortSheet:CreateRectangle:1", "ZSize"),
                layout["gap_length_mm"], failures=failures)

    air = to_floats(prop(editor, "AirBox:CreateBox:1", "Position"))
    check_close("air X", air[0] if air else None, layout["air_x_mm"], failures=failures)
    check_close("air XSize", prop(editor, "AirBox:CreateBox:1", "XSize"),
                layout["air_size_xy_mm"], failures=failures)
    check_close("air ZSize", prop(editor, "AirBox:CreateBox:1", "ZSize"),
                layout["air_size_z_mm"], failures=failures)

    return layout, failures


def main():
    pythoncom.CoInitialize()
    try:
        all_ok = True

        for name, validator in (("PATCH", validate_patch),
                                 ("MONOPOLE", validate_monopole),
                                 ("DIPOLE", validate_dipole)):
            print(f"\n=== {name} ===")
            print(f"{'f GHz':>7} {'lam0':>8} {'key dim':>10} {'board/box':>16} "
                  f"{'result':>8}")
            for freq in FREQUENCIES:
                layout, failures = validator(freq)

                if name == "PATCH":
                    key = f"{layout['feed_width_mm']}x{layout['feed_length_mm']}"
                    size = (f"{layout['board_x_mm']:.1f}x"
                            f"{layout['board_y_mm']:.1f}")
                elif name == "MONOPOLE":
                    key = f"{layout['monopole_length_mm']}"
                    size = f"gnd {layout['ground_half_mm']:.0f}"
                else:
                    key = f"{layout['dipole_length_mm']}"
                    size = f"box {layout['air_size_xy_mm']:.0f}"

                status = "OK" if not failures else "FAIL"
                if failures:
                    all_ok = False

                print(f"{freq:>7} {layout['lambda0_mm']:>8.1f} {key:>10} "
                      f"{size:>16} {status:>8}")

                for problem in failures:
                    print(f"        ! {problem}")

        print("\nRESULT:", "all antennas valid at all frequencies"
              if all_ok else "geometry problems found")
        return 0 if all_ok else 1
    finally:
        pythoncom.CoUninitialize()


if __name__ == "__main__":
    raise SystemExit(main())
