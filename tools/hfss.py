import win32com.client


def create_project():

    app = win32com.client.Dispatch(
        "Ansoft.ElectronicsDesktop"
    )

    desktop = app.GetAppDesktop()

    project = desktop.NewProject()

    project.InsertDesign(
        "HFSS",
        "PatchAntenna",
        "DrivenModal",
        ""
    )

    return {
        "status": "HFSS project and design created"
    }
