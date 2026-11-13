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
