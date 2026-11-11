import win32com.client

oAnsoftApp = win32com.client.Dispatch(
    "Ansoft.ElectronicsDesktop"
)

oDesktop = oAnsoftApp.GetAppDesktop()

oDesktop.NewProject()

print("HFSS Project Created")