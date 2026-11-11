from fastapi import FastAPI
from pydantic import BaseModel
from backend.claude_client import ask_claude
from tools.ads import ads_status, launch_ads
from tools.hfss_com import create_project
from tools.antenna_library import SUBSTRATES
from tools.antenna_calcs import patch_dimensions

 

app = FastAPI()

class AntennaRequest(BaseModel):
    antenna_type: str
    frequency_ghz: float
    substrate: str
    thickness_mm: float


class DesignRequest(BaseModel):

    prompt: str

class AntennaRequest(BaseModel):
    antenna_type: str
    frequency_ghz: float
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


@app.get("/hfss/launch")
def run_hfss():
    return launch_hfss()

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

@app.post("/hfss/create_antenna")
def create_antenna(req: AntennaRequest):

    return {
        "antenna_type": req.antenna_type,
        "frequency_ghz": req.frequency_ghz,
        "substrate": req.substrate,
        "thickness_mm": req.thickness_mm
    }
@app.post("/hfss/build_patch")
def build_patch():
    return {
        "status": "Patch antenna build endpoint ready"
    }