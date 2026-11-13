from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os

from backend.claude_client import ask_claude
from tools.antenna_library import SUBSTRATES
from tools.antenna_calcs import patch_dimensions, patch_layout
from tools.design_params import (
    make_design_params,
    save_design,
    load_design,
    list_designs,
    build_from_params,
)
from tools.hfss_com import (
    create_project,
    create_patch_antenna,
    create_monopole_antenna,
    create_dipole_antenna,
    create_yagi_uda_antenna_prototype,
    simulate_antenna,
)
app = FastAPI()

static_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "static",
)
app.mount("/ui", StaticFiles(directory=static_dir, html=True), name="ui")


from pydantic import BaseModel

class YagiPrototypeRequest(BaseModel):
    frequency_ghz: float = 2.5

class DipoleRequest(BaseModel):
    frequency_ghz: float = 2.4

class MonopoleRequest(BaseModel):
    frequency_ghz: float = 2.4

class DesignRequest(BaseModel):
    prompt: str


class AntennaRequest(BaseModel):
    antenna_type: str
    frequency_ghz: float = 2.4
    substrate: str = "FR4"
    thickness_mm: float = 1.6
    design: str = None          # optional: name of a saved design set


class AntennaSimulateRequest(BaseModel):
    antenna_type: str = "monopole"
    frequency_ghz: float = 2.4
    substrate: str = "FR4"
    thickness_mm: float = 1.6
    span_ghz: float = 0.5
    sweep_count: int = 101
    port_count: int = 1
    solve: bool = True
    results_dir: str = None
    project_path: str = None


class DesignParamsRequest(BaseModel):
    name: str
    antenna_type: str = "patch"
    frequency_ghz: float = 2.4
    substrate: str = "FR4"
    thickness_mm: float = None
    feed_type: str = "edge_inset"
    patch_width_mm: float = None
    patch_length_mm: float = None
    radiator_radius_mm: float = None
    save: bool = True


class BuildFromDesignRequest(BaseModel):
    name: str


@app.get("/")
def root():
    return {
        "message": "CircuitGen API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }


@app.get("/tools")
def tools():
    return {
        "tools": [
            "hfss",
        ]
    }


@app.post("/design")
def design(req: DesignRequest):

    result = ask_claude(req.prompt)

    return {
        "response": result
    }


@app.get("/hfss/new_project")
def hfss_new_project():
    return create_project()


@app.get("/hfss/create_design")
def hfss_create_design():
    return create_project()


@app.post("/hfss/create_antenna")
def create_antenna(req: AntennaRequest):

    substrate = SUBSTRATES[req.substrate]

    if req.antenna_type.lower() == "patch":

        layout = patch_layout(
            req.frequency_ghz,
            er=substrate["er"],
            h_mm=req.thickness_mm,
        )

        return {
            "antenna": "patch",
            "substrate": req.substrate,
            "frequency_ghz": req.frequency_ghz,
            "dimensions": layout,
            "geometry_checks": layout["checks"] or ["all geometric checks passed"],
        }

    return {
        "error": "antenna type not implemented"
    }


@app.post("/hfss/build_patch")
def build_patch(req: AntennaRequest):

    substrate = SUBSTRATES[req.substrate]

    return create_patch_antenna(
        frequency_ghz=req.frequency_ghz,
        thickness_mm=req.thickness_mm,
        er=substrate["er"],
        substrate=req.substrate,
    )

@app.post("/hfss/build_monopole")
def build_monopole(request: MonopoleRequest):

    result = create_monopole_antenna(
        frequency_ghz=request.frequency_ghz
    )

    return result

@app.post("/hfss/build_dipole")
def build_dipole(request: DipoleRequest):

    return create_dipole_antenna(
        frequency_ghz=request.frequency_ghz
    )

@app.post("/hfss/build_yagi_prototype")
def build_yagi_prototype(
    request: YagiPrototypeRequest
):

    return create_yagi_uda_antenna_prototype(
        frequency_ghz=request.frequency_ghz
    )


@app.post("/hfss/build")
def build_antenna(req: AntennaRequest):

    antenna_type = req.antenna_type.lower()

    # build from a saved design parameter set when one is named
    if req.design:
        try:
            params = load_design(req.design)
        except FileNotFoundError as exc:
            return {"error": str(exc)}

        try:
            return build_from_params(params)
        except ValueError as exc:
            return {"error": str(exc)}

    # otherwise derive a parameter set from the request and build from it
    params = make_design_params(
        name=f"{antenna_type}_{req.frequency_ghz}GHz",
        antenna_type=antenna_type,
        frequency_ghz=req.frequency_ghz,
        substrate=req.substrate,
        thickness_mm=req.thickness_mm,
    )

    try:
        result = build_from_params(params)
    except ValueError as exc:
        return {"error": str(exc)}

    result["design_parameters"] = params
    return result


@app.post("/hfss/simulate")
def simulate(req: AntennaSimulateRequest):
    """Build an antenna, solve it in HFSS and return the S parameters."""

    antenna_type = req.antenna_type.lower()

    build_kwargs = {}

    if antenna_type == "patch":
        substrate = SUBSTRATES.get(req.substrate)
        if substrate is None:
            return {"error": f"unknown substrate: {req.substrate}"}
        build_kwargs = {
            "thickness_mm": req.thickness_mm,
            "er": substrate["er"],
            "substrate": req.substrate,
        }

    try:
        result = simulate_antenna(
            antenna_type=antenna_type,
            frequency_ghz=req.frequency_ghz,
            results_dir=req.results_dir,
            project_path=req.project_path,
            port_count=req.port_count,
            span_ghz=req.span_ghz,
            sweep_count=req.sweep_count,
            solve=req.solve,
            **build_kwargs,
        )
    except Exception as exc:      # noqa: BLE001 - report the failure cleanly
        return {
            "error": str(exc),
            "antenna_type": antenna_type,
            "frequency_ghz": req.frequency_ghz,
        }

    simulation = result["simulation"]

    # the raw traces are large, the summary is what callers usually want
    simulation.pop("s_parameters", None)

    return result


# --------------------------------------------------------------------------
# Design parameters - set the design before anything is built
# --------------------------------------------------------------------------

@app.post("/design/params")
def create_design_params(req: DesignParamsRequest):

    params = make_design_params(
        name=req.name,
        antenna_type=req.antenna_type,
        frequency_ghz=req.frequency_ghz,
        substrate=req.substrate,
        thickness_mm=req.thickness_mm,
        feed_type=req.feed_type,
        patch_width_mm=req.patch_width_mm,
        patch_length_mm=req.patch_length_mm,
        radiator_radius_mm=req.radiator_radius_mm,
    )

    saved = None
    if req.save:
        saved = save_design(params)

    return {
        "status": "design parameters ready",
        "saved_to": saved,
        "parameters": params,
    }


@app.get("/design/params")
def get_design_params():
    return {
        "designs": list_designs(),
    }


@app.get("/design/params/{name}")
def get_design_param(name: str):
    try:
        return load_design(name)
    except FileNotFoundError as exc:
        return {"error": str(exc)}


@app.post("/design/build")
def build_from_design(req: BuildFromDesignRequest):

    try:
        params = load_design(req.name)
    except FileNotFoundError as exc:
        return {"error": str(exc)}

    try:
        result = build_from_params(params)
    except ValueError as exc:
        return {"error": str(exc)}

    return {
        "design": params["name"],
        "result": result,
    }
