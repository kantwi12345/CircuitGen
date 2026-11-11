import win32com.client

try:
    app = win32com.client.Dispatch("Ansoft.ElectronicsDesktop")
    print("HFSS COM Connected")
except Exception as e:
    print("ERROR:", e)