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
    design: str = None,
) -> dict:

    payload = {
        "antenna_type": antenna_type,
        "frequency_ghz": frequency_ghz,
        "substrate": substrate,
        "thickness_mm": thickness_mm,
    }
    if design:
        payload["design"] = design

    response = httpx.post(
        f"{API_BASE_URL}/hfss/build",
        json=payload,
        timeout=900,
    )
    response.raise_for_status()

    return response.json()


def create_design_params(
    name: str,
    antenna_type: str = "patch",
    frequency_ghz: float = 2.4,
    substrate: str = "FR4",
    thickness_mm: float = None,
    feed_type: str = "edge_inset",
    patch_width_mm: float = None,
    patch_length_mm: float = None,
    radiator_radius_mm: float = None,
) -> dict:

    payload = {
        "name": name,
        "antenna_type": antenna_type,
        "frequency_ghz": frequency_ghz,
        "substrate": substrate,
        "feed_type": feed_type,
    }
    if thickness_mm is not None:
        payload["thickness_mm"] = thickness_mm
    if patch_width_mm is not None:
        payload["patch_width_mm"] = patch_width_mm
    if patch_length_mm is not None:
        payload["patch_length_mm"] = patch_length_mm
    if radiator_radius_mm is not None:
        payload["radiator_radius_mm"] = radiator_radius_mm

    response = httpx.post(
        f"{API_BASE_URL}/design/params",
        json=payload,
        timeout=120,
    )
    response.raise_for_status()

    return response.json()


def list_design_params() -> dict:
    response = httpx.get(f"{API_BASE_URL}/design/params", timeout=60)
    response.raise_for_status()

    return response.json()


def main(argv=None) -> int:

    parser = argparse.ArgumentParser(
        prog="circuitgen",
        description="CircuitGen build interface - build an antenna in HFSS",
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
    p_antenna.add_argument(
        "--design",
        default=None,
        help="build from a saved design parameter set (see design-params)",
    )

    p_params = subparsers.add_parser(
        "design-params",
        help="Set and save the design parameters before building",
    )
    p_params.add_argument("--name", required=True)
    p_params.add_argument(
        "--antenna-type",
        default="patch",
        choices=["patch", "monopole", "dipole"],
    )
    p_params.add_argument("--frequency-ghz", type=float, default=2.4)
    p_params.add_argument("--substrate", default="FR4")
    p_params.add_argument("--thickness-mm", type=float, default=None)
    p_params.add_argument("--feed-type", default="edge_inset")
    p_params.add_argument("--patch-width-mm", type=float, default=None)
    p_params.add_argument("--patch-length-mm", type=float, default=None)
    p_params.add_argument("--radiator-radius-mm", type=float, default=None)

    p_list = subparsers.add_parser(
        "list-designs",
        help="List the saved design parameter sets",
    )

    args = parser.parse_args(argv)

    if args.command == "build-antenna":

        result = build_antenna(
            antenna_type=args.antenna_type,
            frequency_ghz=args.frequency_ghz,
            substrate=args.substrate,
            thickness_mm=args.thickness_mm,
            design=args.design,
        )
        print(result)
        return 0

    if args.command == "design-params":

        result = create_design_params(
            name=args.name,
            antenna_type=args.antenna_type,
            frequency_ghz=args.frequency_ghz,
            substrate=args.substrate,
            thickness_mm=args.thickness_mm,
            feed_type=args.feed_type,
            patch_width_mm=args.patch_width_mm,
            patch_length_mm=args.patch_length_mm,
            radiator_radius_mm=args.radiator_radius_mm,
        )
        print(result)
        return 0

    if args.command == "list-designs":

        print(list_design_params())
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
