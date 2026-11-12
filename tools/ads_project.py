# tools/ads_project.py

import os

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

WORKSPACE_ROOT = r"C:\ADS_Projects"


def sanitize_workspace_name(name: str) -> str:
    """ADS convention: underscores instead of spaces, no spaces in paths."""

    cleaned = "".join(
        ch if (ch.isalnum() or ch == "_") else "_"
        for ch in str(name).strip()
    )
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")

    return cleaned.strip("_")


def create_ads_workspace(name: str, units: str = "mm"):

    """
    Prepare an ADS 2023 workspace following the documented wizard flow:

      File > New > Workspace
        1. Workspace Name : underscores, no spaces
        2. Directory Path : no spaces
        3. Libraries      : Analog/RF (+ PDKs as required)
        4. Local library  : <workspace>_lib
        5. Technology     : layout units

    The folder tree and the local design library are created here so the
    wizard only has to confirm the values listed in workspace_setup.md.
    """

    workspace_name = sanitize_workspace_name(name)
    library_name = f"{workspace_name}_lib"

    workspace_path = os.path.join(WORKSPACE_ROOT, workspace_name)
    library_path = os.path.join(workspace_path, library_name)

    os.makedirs(library_path, exist_ok=True)

    setup_path = os.path.join(workspace_path, "workspace_setup.md")
    with open(setup_path, "w", encoding="utf-8") as fh:
        fh.write(
            "\n".join(
                [
                    "# ADS Workspace Setup (complete this in ADS 2023)",
                    "",
                    "## File > New > Workspace",
                    "",
                    "| Wizard field | Value to enter |",
                    "|---|---|",
                    f"| Workspace Name | `{workspace_name}` |",
                    f"| Directory Path | `{workspace_path}` |",
                    "| Libraries | Analog/RF (check PDKs if required) |",
                    f"| Local design library | `{library_name}` |",
                    f"| Technology / layout units | {units} |",
                    "",
                    "Steps:",
                    "",
                    "1. Click Create a New Workspace in the Getting Started dialog,",
                    "   or File > New > Workspace in the Main Window.",
                    "2. Enter the Workspace Name and Directory Path above.",
                    "3. Next -> library setup: keep Analog/RF checked.",
                    "4. Next -> confirm the local design library name.",
                    "5. Next -> select the layout units, then Finish.",
                    "",
                    f"The local library folder already exists: {library_path}",
                    "",
                ]
            )
        )

    return {
        "workspace": workspace_path,
        "workspace_name": workspace_name,
        "library": library_path,
        "library_name": library_name,
        "units": units,
        "setup_path": setup_path,
        "status": "created",
    }


class ADSProjectRequest(BaseModel):
    project_name: str
    units: str = "mm"


@app.post("/ads/create_project")
def create_ads_project(req: ADSProjectRequest):

    return create_ads_workspace(req.project_name, req.units)
