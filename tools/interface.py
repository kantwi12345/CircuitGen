import argparse
import os

import httpx

API_BASE_URL = os.environ.get(
    "CIRCUITGEN_API_URL",
    "http://127.0.0.1:8000",
)


def build_antenna(
    antenna_type: str,
    frequency_ghz: float = 2.4,
    substrate: str = "FR4",
    thickness_mm: float = 1.6,
) -> dict:

    payload = {
        "antenna_type": antenna_type,
        "frequency_ghz": frequency_ghz,
        "substrate": substrate,
        "thickness_mm": thickness_mm,
    }

    response = httpx.post(
        f"{API_BASE_URL}/hfss/build",
        json=payload,
        timeout=900,
    )
    response.raise_for_status()

    return response.json()


def build_circuit(
    circuit_type: str,
    frequency_ghz: float = 2.4,
) -> dict:

    response = httpx.post(
        f"{API_BASE_URL}/ads/build",
        json={
            "circuit_type": circuit_type,
            "frequency_ghz": frequency_ghz,
        },
        timeout=300,
    )
    response.raise_for_status()

    return response.json()


def main(argv=None) -> int:

    parser = argparse.ArgumentParser(
        prog="circuitgen",
        description=(
            "CircuitGen build interface - build an antenna in HFSS "
            "or a circuit in ADS"
        ),
    )
    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    p_antenna = subparsers.add_parser(
        "build-antenna",
        help="Build an antenna in HFSS",
    )
    p_antenna.add_argument(
        "--antenna-type",
        required=True,
        choices=["patch", "monopole", "dipole", "yagi"],
    )
    p_antenna.add_argument("--frequency-ghz", type=float, default=2.4)
    p_antenna.add_argument("--substrate", default="FR4")
    p_antenna.add_argument("--thickness-mm", type=float, default=1.6)

    p_circuit = subparsers.add_parser(
        "build-circuit",
        help="Build a circuit in ADS (passive / active)",
    )
    p_circuit.add_argument(
        "--circuit-type",
        required=True,
        choices=["passive", "active"],
    )
    p_circuit.add_argument("--frequency-ghz", type=float, default=2.4)

    args = parser.parse_args(argv)

    if args.command == "build-antenna":

        result = build_antenna(
            antenna_type=args.antenna_type,
            frequency_ghz=args.frequency_ghz,
            substrate=args.substrate,
            thickness_mm=args.thickness_mm,
        )
        print(result)
        return 0

    if args.command == "build-circuit":

        result = build_circuit(
            circuit_type=args.circuit_type,
            frequency_ghz=args.frequency_ghz,
        )
        print(result)
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
