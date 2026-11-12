# tools/ads_project.py

import os
from pydantic import BaseModel
from fastapi import FastAPI

app = FastAPI()

WORKSPACE_ROOT = r"C:\CircuitGen\projects"


def create_ads_workspace(name):

    workspace = os.path.join(WORKSPACE_ROOT, name)

    os.makedirs(workspace, exist_ok=True)

    return {
        "workspace": workspace,
        "status": "created"
    }


class ADSProjectRequest(BaseModel):
    project_name: str


@app.post("/ads/create_project")
def create_ads_project(req: ADSProjectRequest):

    return create_ads_workspace(req.project_name)
