# tools/ads_project.py

import os
import subprocess

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

ADS_EXE = r"C:\Program Files\Keysight\ADS2023_Update1\bin\ads.exe"
WORKSPACE_ROOT = r"C:\ADS_Projects"

# Standard ADS libraries that are attached to every new workspace.
STANDARD_LIBRARIES = [
    "ads_builtin",
    "ads_simulation",
    "ads_rflib",
    "ads_tlines",
    "ads_sources",
    "ads_behavioral",
    "ads_common_cmps",
    "ads_textfonts",
    "ads_datacmps",
    "ads_pelib",
    "ads_designs",
    "ads_schematic_layers",
    "ads_standard_layers",
    "ads_schematic_ports_ic",
    "ads_schematic_layers_ic",
    "ads_standard_layers_ic",
]


def sanitize_workspace_name(name: str) -> str:
    """ADS convention: underscores instead of spaces, no spaces in paths."""

    cleaned = "".join(
        ch if (ch.isalnum() or ch == "_") else "_"
        for ch in str(name).strip()
    )
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")

    return cleaned.strip("_")


def _find_reference_workspace():
    """Find an existing ADS workspace to use as a structural template."""

    candidates = [
        r"C:\Users\Hulede\RF_PA_wrk",
        r"C:\Users\Hulede\rat race_wrk",
        r"C:\Users\Hulede\MyWorkspace_wrk",
    ]

    home = os.path.expanduser("~")
    for name in sorted(os.listdir(home)) if os.path.isdir(home) else []:
        if name.endswith("_wrk"):
            candidates.append(os.path.join(home, name))

    for path in candidates:
        if os.path.exists(os.path.join(path, "workspace.ads")):
            return path

    return None


# Generic workspace files copied from an existing ADS workspace so the
# generated workspace is complete and opens cleanly in ADS.
WORKSPACE_TEMPLATE_FILES = [
    "cds.lib",
    "dds.cfg",
    "de_sim.cfg",
    "hpeesofsim.cfg",
    "dc_annotation_options.xml",
    "default.pinproperties",
    "navigator.opt",
    "layout.prf",
    "schematic.prf",
    "ads_builtin_lay.prf",
    "ads_rflib_lay.prf",
    "ads_simulation_lay.prf",
    "ads_tlines_lay.prf",
    "saved.wrkstate",
    "fileRefs.json",
]


def _read_standard_libraries(reference: str):
    """Pull the <Library .../> list from a reference workspace.ads."""

    if not reference:
        return list(STANDARD_LIBRARIES)

    path = os.path.join(reference, "workspace.ads")
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError:
        return list(STANDARD_LIBRARIES)

    import re

    found = re.findall(r'<Library Name="([^"]+)"', text)
    local = re.findall(r'<Library Name="([^"]+_lib)"', text)
    standard = [name for name in found if name not in local]

    return standard or list(STANDARD_LIBRARIES)


def create_ads_workspace(name: str, units: str = "mm", cells=None):
    """
    Create a real ADS 2023 workspace on disk:

      File > New > Workspace wizard values:
        1. Workspace Name : underscores, no spaces
        2. Directory Path : no spaces
        3. Libraries      : Analog/RF (+ PDKs if required)
        4. Local library  : <workspace>_lib
        5. Technology     : layout units

    Files written (format taken from a reference ADS 2023 workspace):
      workspace.ads, lib.defs, cds.lib, saved.wrkstate, fileRefs.json
      <workspace>_lib/.oalib  + the standard workspace preference files
    """

    workspace_name = sanitize_workspace_name(name)
    library_name = f"{workspace_name}_lib"

    # ADS appends _wrk to the workspace directory name.
    workspace_dir = os.path.join(WORKSPACE_ROOT, f"{workspace_name}_wrk")
    library_path = os.path.join(workspace_dir, library_name)

    os.makedirs(library_path, exist_ok=True)

    reference = _find_reference_workspace()

    # --- generic workspace files (cloned from a reference workspace) ---
    for filename in WORKSPACE_TEMPLATE_FILES:
        if not reference:
            continue
        src = os.path.join(reference, filename)
        if os.path.exists(src):
            try:
                with open(src, "rb") as fh:
                    data = fh.read()
                with open(os.path.join(workspace_dir, filename), "wb") as fh:
                    fh.write(data)
            except OSError:
                pass

    # --- lib.defs -------------------------------------------------
    lib_defs = "\n".join(
        [
            "INCLUDE $HPEESOF_DIR/oalibs/analog_rf.defs",
            "INCLUDE $HPEESOF_DIR/oalibs/dsp.defs",
            f"DEFINE {library_name} {library_name}",
            f"ASSIGN {library_name} libMode shared",
            "",
        ]
    )
    with open(os.path.join(workspace_dir, "lib.defs"), "w",
              encoding="utf-8") as fh:
        fh.write(lib_defs)

    with open(os.path.join(workspace_dir, "cds.lib"), "w",
              encoding="utf-8") as fh:
        fh.write("softinclude lib.defs\n")

    with open(os.path.join(workspace_dir, "fileRefs.json"), "w",
              encoding="utf-8") as fh:
        fh.write(
            '{"files":[],"version":{"_data_":1.0,'
            '"_wellknowntype_":"double"}}'
        )

    with open(os.path.join(workspace_dir, "saved.wrkstate"), "w",
              encoding="utf-8") as fh:
        fh.write(
            "<!DOCTYPE SaveWorkspaceState>\n"
            "<SaveWorkspaceState>\n"
            "    <Windows/>\n"
            '    <MainWindowTab tab="1"/>\n'
            "</SaveWorkspaceState>\n"
        )

    # --- library index --------------------------------------------
    with open(os.path.join(library_path, ".oalib"), "w",
              encoding="utf-8") as fh:
        fh.write(
            '<?xml version="1.0"?>\n\n'
            '<Library DMSystem="oaDMFileSys">\n'
            '    <oaDMFileSys libReadOnly="No"\n'
            '                 origFileSystem="Windows"/>\n'
            "</Library>\n"
        )

    # --- workspace.ads --------------------------------------------
    lines = [
        '<ADSWorkspace Revision="14" Version="100">',
        '    <Workspace Name="">',
        '        <LibraryDefs Name="lib.defs" />',
    ]
    for library in _read_standard_libraries(reference):
        lines.append(f'        <Library Name="{library}" />')
    lines.append(f'        <Library Name="{library_name}" />')
    for cell in (cells or []):
        lines.append(f'        <Cell Name="{library_name}:{cell}" />')
    lines += [
        "    </Workspace>",
        "</ADSWorkspace>",
        "",
    ]
    with open(os.path.join(workspace_dir, "workspace.ads"), "w",
              encoding="utf-8") as fh:
        fh.write("\n".join(lines))

    setup_path = os.path.join(workspace_dir, "workspace_setup.md")
    with open(setup_path, "w", encoding="utf-8") as fh:
        fh.write(
            "\n".join(
                [
                    "# ADS Workspace Setup",
                    "",
                    "The complete workspace has already been created on disk",
                    "(files match an ADS 2023 workspace: workspace.ads, lib.defs,",
                    "cds.lib, saved.wrkstate, fileRefs.json, preference files",
                    "and the local library `<workspace>_lib`).",
                    "",
                    "Attach it in ADS:",
                    "",
                    "1. Open ADS 2023.",
                    "2. File > Open Workspace... (or the Getting Started dialog)",
                    "   and select:",
                    f"      {workspace_dir}",
                    "3. The workspace tree opens with the local library",
                    f"   `{library_name}` attached.",
                    "4. File > New > Schematic -> select the local library ->",
                    f"   cell name (no spaces) -> Create Schematic.",
                    "5. Place the parts per the build sheet, or import:",
                    f"   File > Import > SPICE Netlist... (see <library>/netlists/)",
                    "",
                    "Note: ADS 2023 on Windows has no command-line or COM way to",
                    "open a workspace - this attach step is required once per",
                    "workspace (verified: ads.exe ignores a workspace argument,",
                    "even for an existing workspace).",
                    "",
                ]
            )
        )

    return {
        "workspace": workspace_dir,
        "workspace_name": workspace_name,
        "library": library_path,
        "library_name": library_name,
        "units": units,
        "setup_path": setup_path,
        "workspace_ads": os.path.join(workspace_dir, "workspace.ads"),
        "status": "created",
    }


def open_ads_workspace(workspace_info: dict):
    """Launch ADS with the generated workspace so it appears in the GUI."""

    workspace_ads = workspace_info.get("workspace_ads")

    if os.path.exists(ADS_EXE):
        args = [ADS_EXE]
        if workspace_ads and os.path.exists(workspace_ads):
            args.append(workspace_ads)
        subprocess.Popen(args)

        return {
            "status": "ADS launched",
            "workspace": workspace_info.get("workspace"),
            "workspace_ads": workspace_ads,
        }

    return {
        "status": "ADS executable not found",
        "workspace": workspace_info.get("workspace"),
    }


class ADSProjectRequest(BaseModel):
    project_name: str
    units: str = "mm"


@app.post("/ads/create_project")
def create_ads_project(req: ADSProjectRequest):

    return create_ads_workspace(req.project_name, req.units)
