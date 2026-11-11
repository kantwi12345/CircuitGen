from fastapi import FastAPI
from pydantic import BaseModel

from backend.claude_client import ask_claude
from tools.ads import ads_status, launch_ads
from tools.antenna_library import SUBSTRATES
from tools.antenna_calcs import patch_dimensions
from tools.hfss_com import create_project, create_patch_antenna

app = FastAPI()


class DesignRequest(BaseModel):
    prompt: str


class AntennaRequest(BaseModel):
    antenna_type: str
    frequency_ghz: float = 2.4
    substrate: str = "FR4"
    thickness_mm: float = 1.6


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