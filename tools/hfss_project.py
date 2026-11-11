# tools/hfss_project.py

import os

PROJECT_ROOT = r"C:\CircuitGen\hfss_projects"


def create_hfss_project(name):

    project_folder = os.path.join(PROJECT_ROOT, name)

    os.makedirs(project_folder, exist_ok=True)

    return {
        "project": project_folder,
        "status": "created"
    }
class HFSSProjectRequest(BaseModel):
    project_name: str


@app.post("/hfss/create_project")
def create_hfss(req: HFSSProjectRequest):

    from tools.hfss_project import create_hfss_project

    return create_hfss_project(req.project_name)