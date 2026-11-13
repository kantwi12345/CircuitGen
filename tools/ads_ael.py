"""
CircuitGen - ADS AEL macro generator.

ADS macros are AEL scripts (ADS records them as *.mac / *.dem). The
design-editor API used here was taken from the ADS AEL sources and from
a recorded ADS macro (one resistor, placed + value set):

    decl macroContext = de_create_new_schematic_view("LNA_lib", "lna", "schematic");
    de_show_context_in_new_window(macroContext);
    decl macroContext = de_get_design_context_from_name("LNA_lib:lna:schematic");
    de_show_context_in_new_window(macroContext);
    de_close_window();
    decl macroContext = de_get_design_context_from_name("LNA_lib:lna:schematic");
    de_show_context_in_new_window(macroContext);
    decl itemInfo1SP = de_init_item("ads_rflib:R:symbol");
    de_place_item(itemInfo1SP, 0.25, 0.5);
    itemInfo1SP = de_free_item(itemInfo1SP);
    de_select_range(0.74375, 0.46875, 0.74375, 0.46875, 1, 1);
    decl itemInfo1SP = de_edit_item("R1");
    de_set_item_parameters(itemInfo1SP, list(prm_ex("ads_rflib","StdForm","30 Ohm"), ...));
    de_end_edit_item(itemInfo1SP);
    de_end_edit_item(itemInfo1SP);
    de_end_edit_item(itemInfo1SP);
    itemInfo1SP = de_free_item(itemInfo1SP);
"""

import os

from tools.netlist_sim import parse_netlist

COMPONENT_TYPES = {
    "R": "R",
    "C": "C",
    "L": "L",
    "V": "V_DC",
    "I": "I_DC",
    "E": "VCVS",
    "G": "VCCS",
}

GRID_X = 1.0
GRID_Y = 0.6
ORIGIN_X = 1.0
ORIGIN_Y = 0.5


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
            return f"{value/1e-6:g} uH"
        if abs(value) >= 1e-9:
            return f"{value*1e9:g} nH"
        return f"{value*1e12:g} pH"
    if kind == "C":
        if abs(value) >= 1e-6:
            return f"{value/1e-6:g} uF"
        if abs(value) >= 1e-9:
            return f"{value*1e9:g} nF"
        if abs(value) >= 1e-12:
            return f"{value*1e12:g} pF"
        return f"{value*1e15:g} fF"
    return f"{value:g}"


def build_macro(
    library: str,
    cell: str,
    netlist_text: str,
    include_wires: bool = True,
) -> str:

    elements = parse_netlist(netlist_text)

    positions = {}
    column = 0
    row = 0
    for element in elements:
        if element.kind not in COMPONENT_TYPES:
            continue
        positions[element.name] = (column * GRID_X, row * GRID_Y)
        column += 1
        if column >= 4:
            column = 0
            row += 1

    # auto-assigned instance names: R1, R2, C1, C2, ...
    counters = {}
    instance_names = {}
    for element in elements:
        if element.kind not in COMPONENT_TYPES:
            continue
        counters[element.kind] = counters.get(element.kind, 0) + 1
        instance_names[element.name] = (
            f"{COMPONENT_TYPES[element.kind][0]}{counters[element.kind]}"
        )

    full_cell = f"{library}:{cell}:schematic"

    lines = [
        "/* Begin */",
        f'decl macroContext = de_create_new_schematic_view("{library}", '
        f'"{cell}", "schematic");',
        "de_show_context_in_new_window(macroContext);",
        f'decl macroContext = de_get_design_context_from_name("{full_cell}");',
        "// For an artwork macro: decl macroContext = de_get_current_design_context();",
        "de_show_context_in_new_window(macroContext);",
        "de_close_window();",
        "/* Begin */",
        f'decl macroContext = de_get_design_context_from_name("{full_cell}");',
        "// For an artwork macro: decl macroContext = de_get_current_design_context();",
        "de_show_context_in_new_window(macroContext);",
        "",
    ]

    # ---- place + value-set each component ---------------------------
    for element in elements:
        kind = element.kind
        if kind not in COMPONENT_TYPES:
            continue

        x = ORIGIN_X + positions[element.name][0]
        y = ORIGIN_Y + positions[element.name][1]
        cx = x + 0.5
        cy = y + 0.02
        symbol = f"ads_rflib:{COMPONENT_TYPES[kind]}:symbol"

        if kind in ("R", "C", "L"):
            value = _format_value(element.params.get("value"), kind)
        elif kind in ("V", "I"):
            value = f"DC={element.params.get('dc', 0.0)} Volt"
        else:
            value = f"gain={element.params.get('gain', 0)}"

        inst = instance_names[element.name]

        lines.append(f'decl itemInfo0SP = de_init_item("{symbol}");')
        lines.append(f"de_place_item(itemInfo0SP, {x:g}, {y:g});")
        lines.append("itemInfo0SP = de_free_item(itemInfo0SP);")
        lines.append(f"de_select_range({cx:g}, {cy:g}, {cx:g}, {cy:g}, 1, 1);")
        lines.append(f'decl itemInfo0SP = de_edit_item("{inst}");')
        lines.append(
            f'de_set_item_parameters(itemInfo0SP, '
            f'list(prm_ex("ads_rflib","StdForm","{value}")));'
        )
        lines.append("de_end_edit_item(itemInfo0SP);")
        lines.append("de_end_edit_item(itemInfo0SP);")
        lines.append("de_end_edit_item(itemInfo0SP);")
        lines.append("itemInfo0SP = de_free_item(itemInfo0SP);")
        lines.append("")

    # ---- connect the parts with wires (best effort) -----------------
    if include_wires:
        lines.append("/* --- connections --- */")
        nets = {}
        for element in elements:
            if element.kind in ("R", "C", "L", "V", "I"):
                for index, node in enumerate(element.nodes):
                    nets.setdefault(node, []).append((element.name, index))

        for node, members in nets.items():
            if node == "0" or len(members) < 2:
                continue
            lines.append(f'set_named_connection("{node}");')
            for name, _ in members:
                x, y = positions.get(name, (0, 0))
                cx = ORIGIN_X + x + 0.5
                cy = ORIGIN_Y + y + 0.02
                lines.append(f"named_connection({cx:g}, {cy:g});")
            lines.append("ifftolib_set_layer(4, 1);")
            first_name, _ = members[0]
            fx, fy = positions.get(first_name, (0, 0))
            lines.append(f"add_wire({ORIGIN_X + fx + 0.5:g}, "
                        f"{ORIGIN_Y + fy + 0.02:g});")
            for name, _ in members[1:]:
                x, y = positions.get(name, (0, 0))
                lines.append(f"add_wire({ORIGIN_X + x + 0.5:g}, "
                            f"{ORIGIN_Y + y + 0.02:g});")
            lines.append("end();")
            lines.append("")

    lines.append("de_save();")
    lines.append("/* End */")
    lines.append("")

    return "\n".join(lines)


def write_macro(path, library, cell, netlist_text, include_wires=True):
    macro = build_macro(library, cell, netlist_text, include_wires)

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(macro)

    dem_path = path + ".dem"
    with open(dem_path, "w", encoding="utf-8") as fh:
        fh.write(macro)

    return path
