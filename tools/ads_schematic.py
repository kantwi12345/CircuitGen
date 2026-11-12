# tools/ads_schematic.py

import os

from tools.netlist_sim import parse_netlist

PALETTE = {
    "R": ("Lumped-Components", "Resistor"),
    "C": ("Lumped-Components", "Capacitor"),
    "L": ("Lumped-Components", "Inductor"),
    "V": ("Sources", "DC Voltage Source / Vtone"),
    "I": ("Sources", "DC Current Source / Itone"),
    "E": ("Sources", "Voltage Controlled Voltage Source"),
    "G": ("Sources", "Voltage Controlled Current Source"),
}


def cell_name_for(design: str) -> str:
    """ADS cell names must not contain spaces."""

    cleaned = "".join(
        ch if (ch.isalnum() or ch == "_") else "_"
        for ch in str(design).strip().lower()
    )
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")

    return cleaned.strip("_")


def extract_parts(netlist_text: str):
    """Return (parts, nets) from a netlist."""

    elements = parse_netlist(netlist_text)

    parts = []
    nets = {}

    for element in elements:
        palette, part = PALETTE.get(
            element.kind, ("Lumped-Components", element.kind)
        )

        value = element.params.get("value")
        if value is None and element.kind in ("V", "I"):
            value = element.params.get("ac", 0.0)

        if element.kind in ("V", "I"):
            value_text = f"DC {element.params.get('dc', 0.0)} / AC {element.params.get('ac', 0.0)}"
        elif element.kind in ("E", "G"):
            value_text = f"gain = {element.params['gain']}"
        else:
            value_text = _format_value(value, element.kind)

        parts.append({
            "refdes": element.name,
            "type": element.kind,
            "palette": palette,
            "part": part,
            "value": value_text,
        })

        if element.kind in ("R", "C", "L", "V", "I"):
            pins = {element.nodes[0]: "+", element.nodes[1]: "-"}
            for node in element.nodes:
                nets.setdefault(node, []).append(f"{element.name}.{pins[node]}")
        else:
            pins = {
                element.nodes[0]: "+",
                element.nodes[1]: "-",
                element.nodes[2]: "c+",
                element.nodes[3]: "c-",
            }
            for node in element.nodes:
                nets.setdefault(node, []).append(f"{element.name}.{pins[node]}")

    return parts, nets


def _format_value(value, kind: str = "R") -> str:
    if value is None:
        return "-"

    value = float(value)

    if kind == "R":
        for suffix, scale in (("k", 1e3), ("M", 1e6)):
            if abs(value) >= scale:
                return f"{value / scale:g} {suffix}Ohm"
        return f"{value:g} Ohm"

    if kind == "L":
        for suffix, scale in (("u", 1e-6), ("n", 1e-11), ("p", 1e-13)):
            if abs(value) >= scale:
                return f"{value / scale:g} {suffix}H"
        return f"{value:g} H"

    if kind == "C":
        for suffix, scale in (("u", 1e-6), ("n", 1e-11), ("p", 1e-13),
                              ("f", 1e-15)):
            if abs(value) >= scale:
                return f"{value / scale:g} {suffix}F"
        return f"{value:g} F"

    return f"{value:g}"


def build_schematic_build_sheet(
    design: str,
    cell: str,
    netlist_text: str,
    library_name: str,
    units: str = "mm",
) -> str:
    """Build sheet that drives the ADS schematic creation GUI steps."""

    parts, nets = extract_parts(netlist_text)

    lines = [
        f"# ADS Schematic Build Sheet - {design}",
        "",
        "Follow the ADS 2023 schematic creation flow below and place the",
        "parts listed in the tables.",
        "",
        "## 1. New schematic",
        "",
        "| Field | Value |",
        "|---|---|",
        "| Action | File > New > Schematic (or the New Schematic toolbar icon) |",
        f"| Library | `{library_name}` (local design library) |",
        f"| Cell Name | `{cell}` (no spaces) |",
        "",
        "## 2. Palette",
        "",
        "Use the Palette drop-down in the schematic window (top left):",
        "",
        "| Part type used | Palette | Palette item |",
        "|---|---|---|",
    ]

    seen = set()
    for part in parts:
        key = (part["palette"], part["part"])
        if key in seen:
            continue
        seen.add(key)
        lines.append(f"| {part['type']} | {part['palette']} | {part['part']} |")

    lines += [
        "",
        "## 3. Parts and values",
        "",
        "Click the parameter text next to a placed part (e.g. `R=50 Ohm`) and",
        "type the value below. Press Ctrl+R before or after clicking to",
        "rotate a part by 90 degrees, Esc to exit placement mode.",
        "",
        "| RefDes | Type | Value | Palette item |",
        "|---|---|---|---|",
    ]

    for part in parts:
        lines.append(
            f"| {part['refdes']} | {part['type']} | `{part['value']}` "
            f"| {part['palette']} / {part['part']} |"
        )

    lines += [
        "",
        "## 4. Wiring (Ctrl+W)",
        "",
        "Start the wire on a red pin and end it on the pin of the next part.",
        "Every connection below must exist in the schematic.",
        "",
        "| Net | Pins |",
        "|---|---|",
    ]

    for node in sorted(nets):
        pins = ", ".join(sorted(nets[node]))
        if node == "0":
            lines.append(f"| GND | {pins} |")
        else:
            lines.append(f"| {node} | {pins} |")

    grounds = [n for n in nets if n == "0"]
    lines += [
        "",
        "## 5. Ground",
        "",
        "Click the Insert Ground icon (triangle) on the top toolbar and place",
        "a ground on the GND net.",
        "",
        "| Net | Pins requiring ground |",
        "|---|---|",
    ]
    for node in grounds:
        lines.append(f"| {node} | {', '.join(sorted(nets[node]))} |")

    lines += [
        "",
        "## 6. Save",
        "",
        "File > Save (Ctrl+S) to save the schematic cell in the local library.",
        "",
        f"Layout units for this workspace: **{units}**",
        "",
        "## 7. Simulation setup (after the schematic is saved)",
        "",
        "1. Simulation > Setup Simulation / New Simulation > S-Parameter.",
        "2. Add ports: TermG at the input net and at the output/load net.",
        "3. Sweep the frequency range around the design frequency.",
        "4. Run the analysis and review S11 / S21 / power.",
        "",
        "Note: the matching network netlist is also stored in the library",
        "netlists folder and can be imported if you prefer to start from it.",
        "",
    ]

    return "\n".join(lines)


def write_schematic_build_sheet(
    workspace_info: dict,
    design: str,
    netlist_text: str,
) -> dict:
    """Create the cell folder contents in the local ADS library."""

    cell = cell_name_for(design)
    library_path = workspace_info["library"]
    netlists_dir = os.path.join(library_path, "netlists")
    os.makedirs(netlists_dir, exist_ok=True)

    netlist_path = os.path.join(netlists_dir, f"{cell}.net")
    with open(netlist_path, "w", encoding="utf-8") as fh:
        fh.write(netlist_text)

    sheet = build_schematic_build_sheet(
        design,
        cell,
        netlist_text,
        workspace_info["library_name"],
        workspace_info.get("units", "mm"),
    )
    sheet_path = os.path.join(library_path, f"{cell}_build_sheet.md")
    with open(sheet_path, "w", encoding="utf-8") as fh:
        fh.write(sheet)

    return {
        "cell": cell,
        "library": library_path,
        "library_name": workspace_info.get("library_name", ""),
        "workspace_dir": workspace_info.get("workspace", ""),
        "build_sheet_path": sheet_path,
        "netlist_path": netlist_path,
    }
