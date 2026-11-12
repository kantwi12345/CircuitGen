"""
CircuitGen - ADS AEL macro generator.

ADS macros are AEL scripts (ADS records them as *.mac / *.dem files).
The design-editor API used here was taken from the ADS AEL sources:

    de_create_new_schematic_view(lib, cell, "schematic")
    de_show_context_in_new_window(macroContext)
    de_iff_add_component(type, instName, isLeaf, x, y, rot, mirror, mask, propList)
    place_instance(x, y)
    db_add_string_parm_to_instance(instance, parmName, value)
    add_wire(x, y) ... end();
    set_named_connection(net); named_connection(x, y);

The generated macro is played back inside ADS with
    Tools > Playback Macro...
"""

import math
import os

from tools.netlist_sim import parse_netlist

# ADS palette component names (Lumped-Components / Sources palettes)
COMPONENT_TYPES = {
    "R": "Resistor",
    "C": "Capacitor",
    "L": "Inductor",
    "V": "DC Voltage Source",
    "I": "DC Current Source",
    "E": "Voltage Controlled Voltage Source",
    "G": "Voltage Controlled Current Source",
}

# schematic parameter name per component type
PARAM_NAMES = {
    "R": "R",
    "C": "C",
    "L": "L",
    "V": "DC",
    "I": "DC",
    "E": "gain",
    "G": "gain",
}

GRID_X = 1000
GRID_Y = 1000
ORIGIN_X = 2000
ORIGIN_Y = 2000


def _format_value(value, kind):
    if value is None:
        return ""
    value = float(value)
    if kind == "R":
        if abs(value) >= 1e3:
            return f"{value/1e3:g}k Ohm"
        return f"{value:g} Ohm"
    if kind == "L":
        if abs(value) >= 1e-6:
            return f"{value/1e6:g}u H"
        return f"{value*1e9:g} nH"
    if kind == "C":
        if abs(value) >= 1e-6:
            return f"{value/1e6:g}u F"
        return f"{value*1e12:g} pF"
    return f"{value:g}"


def build_macro(
    library: str,
    cell: str,
    netlist_text: str,
    include_wires: bool = True,
) -> str:
    """Build an AEL macro that recreates the netlist as an ADS schematic."""

    elements = parse_netlist(netlist_text)

    lines = [
        f'/* CircuitGen ADS macro - {library}:{cell} */',
        "",
        f'decl macroContext = de_create_new_schematic_view("{library}", '
        f'"{cell}", "schematic");',
        "de_show_context_in_new_window(macroContext);",
        "",
    ]

    # ---- place the components on a grid -------------------------------
    positions = {}
    column = 0
    row = 0

    for element in elements:
        kind = element.kind
        if kind not in COMPONENT_TYPES:
            continue

        x = ORIGIN_X + column * GRID_X
        y = ORIGIN_Y - row * GRID_Y
        positions[element.name] = (x, y)

        if kind in ("R", "C", "L"):
            value = _format_value(element.params.get("value"), kind)
            prop = f'"{PARAM_NAMES[kind]}={value}"'
        elif kind in ("V", "I"):
            dc = element.params.get("dc", 0.0)
            ac = element.params.get("ac", 0.0)
            prop = f'"DC={dc} Volt"'
        else:
            prop = f'"gain={element.params.get("gain", 0)}"'

        lines.append(
            f'de_iff_add_component("{COMPONENT_TYPES[kind]}", '
            f'"{element.name}", TRUE, {x}, {y}, 0, MIRROR_NONE, 0, list({prop}));'
        )

        column += 1
        if column >= 4:
            column = 0
            row += 1

    lines.append("")

    # ---- connect the parts with wires --------------------------------
    if include_wires:
        nets = {}
        for element in elements:
            if element.kind in ("R", "C", "L", "V", "I"):
                for index, node in enumerate(element.nodes):
                    nets.setdefault(node, []).append((element.name, index))

        lines.append("* --- connections ---")
        for node, members in nets.items():
            if node == "0" or len(members) < 2:
                continue
            for i in range(len(members) - 1):
                (name_a, pin_a), (name_b, pin_b) = members[i], members[i + 1]
                x1, y1 = positions.get(name_a, (ORIGIN_X, ORIGIN_Y))
                x2, y2 = positions.get(name_b, (ORIGIN_X, ORIGIN_Y))
                lines.append(f'set_named_connection("{node}");')
                lines.append(f"named_connection({x1}, {y1});")
                lines.append(f"named_connection({x2}, {y2});")
        lines.append("")

    lines.append("de_save();")
    lines.append("")

    return "\n".join(lines)


def write_macro(
    path: str,
    library: str,
    cell: str,
    netlist_text: str,
    include_wires: bool = True,
) -> str:
    macro = build_macro(library, cell, netlist_text, include_wires)

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(macro)

    # ADS appends .dem to macro names when recording - write both
    dem_path = path + ".dem"
    with open(dem_path, "w", encoding="utf-8") as fh:
        fh.write(macro)

    return path
