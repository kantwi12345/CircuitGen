from fastapi import FastAPI
from pydantic import BaseModel

from backend.claude_client import ask_claude
from tools.ads import ads_status, launch_ads, build_ads_circuit
from tools.antenna_library import SUBSTRATES
from tools.antenna_calcs import patch_dimensions
from tools.hfss_com import (
    create_project,
    create_patch_antenna,
    create_monopole_antenna,
    create_dipole_antenna,
    create_yagi_uda_antenna_prototype
)
app = FastAPI()


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


class ADSBuildRequest(BaseModel):
    circuit_type: str
    frequency_ghz: float = 2.4


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
            "ads",
            "hfss",
            "spice",
            "kicad"
        ]
    }


@app.post("/design")
def design(req: DesignRequest):

    result = ask_claude(req.prompt)

    return {
        "response": result
    }


@app.get("/ads/status")
def get_ads_status():
    return ads_status()


@app.get("/ads/launch")
def run_ads():
    return launch_ads()


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

        dims = patch_dimensions(
            req.frequency_ghz,
            substrate["er"],
            req.thickness_mm
        )

        return {
            "antenna": "patch",
            "substrate": req.substrate,
            "frequency_ghz": req.frequency_ghz,
            "dimensions": dims
        }

    return {
        "error": "antenna type not implemented"
    }


@app.post("/hfss/build_patch")
def build_patch(req: AntennaRequest):

    print("REQ:", req)

    substrate = SUBSTRATES[req.substrate]

    dims = patch_dimensions(
        req.frequency_ghz,
        substrate["er"],
        req.thickness_mm
    )

    return create_patch_antenna(
        dims["width_mm"],
        dims["length_mm"]
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


@app.post("/ads/build")
def build_circuit(req: ADSBuildRequest):

    return build_ads_circuit(
        circuit_type=req.circuit_type,
        frequency_ghz=req.frequency_ghz
    )


@app.post("/hfss/build")
def build_antenna(req: AntennaRequest):

    antenna_type = req.antenna_type.lower()

    if antenna_type == "patch":

        substrate = SUBSTRATES[req.substrate]

        dims = patch_dimensions(
            req.frequency_ghz,
            substrate["er"],
            req.thickness_mm
        )

        return create_patch_antenna(
            dims["width_mm"],
            dims["length_mm"]
        )

    if antenna_type == "monopole":

        return create_monopole_antenna(
            frequency_ghz=req.frequency_ghz
        )

    if antenna_type == "dipole":

        return create_dipole_antenna(
            frequency_ghz=req.frequency_ghz
        )

    if antenna_type == "yagi":

        return create_yagi_uda_antenna_prototype(
            frequency_ghz=req.frequency_ghz
        )

    return {
        "error": "antenna type not implemented"
    }


