"""
CircuitGen - small AC netlist simulator (modified nodal analysis).

This is the working substitute for ADS circuit simulation in environments
where ADS COM automation is unavailable.

Supported elements: R, C, L, V, I, E (VCVS), G (VCCS).
Supported analyses: frequency sweep with node voltages, gain, input
reflection coefficient (S11) and load power.

Supports SPICE-style value suffixes: T G MEG K M U N P F.
"""

import math
import re

import numpy as np

SUFFIXES = {
    "T": 1e12,
    "G": 1e9,
    "MEG": 1e6,
    "K": 1e3,
    "M": 1e-3,
    "U": 1e-6,
    "N": 1e-9,
    "P": 1e-12,
    "F": 1e-15,
}


def parse_value(token: str) -> float:
    """Parse a SPICE value such as 1.15p, 30k, 0.18n, 3.3."""

    text = token.strip().upper()

    match = re.match(r"^([+-]?[0-9]*\.?[0-9]+(?:[Ee][+-]?[0-9]+)?)(.*)$", text)
    if not match:
        raise ValueError(f"cannot parse value: {token}")

    number = float(match.group(1))
    suffix = match.group(2)

    if suffix in SUFFIXES:
        number *= SUFFIXES[suffix]
    elif suffix in ("", "OHM", "F", "H", "V", "A"):
        pass
    else:
        raise ValueError(f"unknown suffix in value: {token}")

    return number


class Element:
    def __init__(self, kind, name, nodes, params):
        self.kind = kind
        self.name = name
        self.nodes = nodes
        self.params = params


def parse_netlist(text: str):
    """Parse a netlist into elements."""

    elements = []

    for raw_line in text.splitlines():
        line = raw_line.split("*")[0].split(";")[0].split("$")[0].strip()
        if not line:
            continue
        if line.startswith("."):
            continue

        tokens = line.split()

        # SPICE style:  "R1 n1 n2 value"   (type is the first token)
        # ADS style:    "RSRC n1 n2 value" (type is the first letter of the name)
        if tokens[0].upper() in ("R", "C", "L", "V", "I", "E", "G"):
            kind = tokens[0].upper()
            name = tokens[1]
            args = tokens[2:]
        else:
            kind = tokens[0][0].upper()
            name = tokens[0]
            args = tokens[1:]

        if kind == "R":
            elements.append(Element(kind, name, args[0:2],
                                    {"value": parse_value(args[2])}))
        elif kind == "C":
            elements.append(Element(kind, name, args[0:2],
                                    {"value": parse_value(args[2])}))
        elif kind == "L":
            elements.append(Element(kind, name, args[0:2],
                                    {"value": parse_value(args[2])}))
        elif kind == "V":
            ac = 0.0
            dc = 0.0
            idx = 2
            while idx < len(args):
                token = args[idx].upper()
                if token == "DC":
                    dc = parse_value(args[idx + 1])
                    idx += 2
                elif token == "AC":
                    ac = parse_value(args[idx + 1]) if idx + 1 < len(args) else 1.0
                    idx += 2
                else:
                    idx += 1
            elements.append(Element(kind, name, args[0:2], {"ac": ac, "dc": dc}))
        elif kind == "I":
            ac = 0.0
            idx = 2
            while idx < len(args):
                if args[idx].upper() == "AC":
                    ac = parse_value(args[idx + 1]) if idx + 1 < len(args) else 1.0
                    idx += 2
                else:
                    idx += 1
            elements.append(Element(kind, name, args[0:2], {"ac": ac}))
        elif kind == "E":
            elements.append(Element(kind, name, args[0:4],
                                    {"gain": parse_value(args[4])}))
        elif kind == "G":
            elements.append(Element(kind, name, args[0:4],
                                    {"gain": parse_value(args[4])}))
        else:
            raise ValueError(f"unsupported element type: {kind}")

    return elements


class Circuit:
    def __init__(self, elements):
        self.elements = elements

        nodes = []
        for element in elements:
            for node in element.nodes:
                if node.upper() != "0" and node not in nodes:
                    nodes.append(node)
        self.nodes = nodes
        self.index = {node: i for i, node in enumerate(nodes)}

        self.branches = []          # elements needing a branch current
        for element in elements:
            if element.kind in ("V", "E", "L"):
                self.branches.append(element)

        self.size = len(nodes) + len(self.branches)

    def _branch_index(self, element):
        return len(self.nodes) + self.branches.index(element)

    def _stamp(self, omega, ac_sources, current_injections):
        size = self.size
        matrix = np.zeros((size, size), dtype=complex)
        rhs = np.zeros(size, dtype=complex)

        for element in self.elements:

            if element.kind in ("R", "C"):
                n1 = self.index.get(element.nodes[0])
                n2 = self.index.get(element.nodes[1])
                if element.kind == "R":
                    y = 1.0 / element.params["value"]
                else:
                    y = 1j * omega * element.params["value"]
                if n1 is not None:
                    matrix[n1, n1] += y
                if n2 is not None:
                    matrix[n2, n2] += y
                if n1 is not None and n2 is not None:
                    matrix[n1, n2] -= y
                    matrix[n2, n1] -= y

            elif element.kind == "L":
                n1 = self.index.get(element.nodes[0])
                n2 = self.index.get(element.nodes[1])
                k = self._branch_index(element)
                if n1 is not None:
                    matrix[n1, k] += 1
                if n2 is not None:
                    matrix[n2, k] -= 1
                matrix[k, n1] += 1 if n1 is not None else 0
                matrix[k, n2] -= 1 if n2 is not None else 0
                matrix[k, k] -= 1j * omega * element.params["value"]

            elif element.kind == "V":
                n1 = self.index.get(element.nodes[0])
                n2 = self.index.get(element.nodes[1])
                k = self._branch_index(element)
                if n1 is not None:
                    matrix[n1, k] += 1
                if n2 is not None:
                    matrix[n2, k] -= 1
                matrix[k, n1] += 1 if n1 is not None else 0
                matrix[k, n2] -= 1 if n2 is not None else 0
                rhs[k] += ac_sources.get(element.name, element.params["ac"])

            elif element.kind == "I":
                n1 = self.index.get(element.nodes[0])
                n2 = self.index.get(element.nodes[1])
                amp = ac_sources.get(element.name, element.params["ac"])
                if n1 is not None:
                    rhs[n1] += amp
                if n2 is not None:
                    rhs[n2] -= amp

            elif element.kind == "E":
                n1 = self.index.get(element.nodes[0])
                n2 = self.index.get(element.nodes[1])
                c1 = self.index.get(element.nodes[2])
                c2 = self.index.get(element.nodes[3])
                k = self._branch_index(element)
                if n1 is not None:
                    matrix[n1, k] += 1
                if n2 is not None:
                    matrix[n2, k] -= 1
                matrix[k, n1] += 1 if n1 is not None else 0
                matrix[k, n2] -= 1 if n2 is not None else 0
                matrix[k, c1] -= element.params["gain"] if c1 is not None else 0
                matrix[k, c2] += element.params["gain"] if c2 is not None else 0

            elif element.kind == "G":
                n1 = self.index.get(element.nodes[0])
                n2 = self.index.get(element.nodes[1])
                c1 = self.index.get(element.nodes[2])
                c2 = self.index.get(element.nodes[3])
                gain = element.params["gain"]
                if n1 is not None:
                    if c1 is not None:
                        matrix[n1, c1] += gain
                    if c2 is not None:
                        matrix[n1, c2] -= gain
                if n2 is not None:
                    if c1 is not None:
                        matrix[n2, c1] -= gain
                    if c2 is not None:
                        matrix[n2, c2] += gain

        for node, amp in current_injections.items():
            idx = self.index.get(node)
            if idx is not None:
                rhs[idx] += amp

        return matrix, rhs

    def solve(self, omega, ac_sources=None, current_injections=None,
              suppress_sources=False):
        ac_sources = ac_sources or {}
        current_injections = current_injections or {}

        if suppress_sources:
            for element in self.elements:
                if element.kind in ("V", "I"):
                    ac_sources.setdefault(element.name, 0.0)

        matrix, rhs = self._stamp(omega, ac_sources, current_injections)
        solution = np.linalg.solve(matrix, rhs)

        voltages = {}
        for node, idx in self.index.items():
            voltages[node] = solution[idx]
        voltages["0"] = 0.0 + 0j

        return voltages

    def impedance_at(self, node, omega):
        """Driving-point impedance at a node (1 A test current)."""

        voltages = self.solve(
            omega,
            current_injections={node: 1.0},
            suppress_sources=True,
        )
        return voltages[node]


def simulate_ac(
    netlist_text: str,
    frequencies,
    port_node: str,
    reference_node: str,
    output_node: str = None,
    source_resistance: float = 50.0,
    load_resistance: float = 50.0,
):
    """Run an AC sweep and return gain, S11 and load power arrays."""

    circuit = Circuit(parse_netlist(netlist_text))

    freqs = np.asarray(frequencies, dtype=float)
    gains = []
    s11 = []
    p_load = []

    for f in freqs:
        omega = 2 * math.pi * f
        voltages = circuit.solve(omega)

        v_ref = voltages.get(reference_node, 0j)
        v_out = voltages.get(output_node, 0j) if output_node else 0j
        v_port = voltages.get(port_node, 0j)
        gains.append(v_out / v_ref if v_ref != 0 else 0j)

        z_in = circuit.impedance_at(port_node, omega)
        s11.append((z_in - source_resistance) / (z_in + source_resistance))

        if output_node:
            p_load.append(abs(v_out) ** 2 / (2.0 * load_resistance))

    return {
        "f": freqs,
        "gain": np.array(gains),
        "s11": np.array(s11),
        "p_load": np.array(p_load),
    }
