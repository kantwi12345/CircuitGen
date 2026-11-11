from ansys.aedt.core import Hfss

hfss = Hfss(
    new_desktop=True,
    non_graphical=False
)

print("HFSS Connected")

hfss.release_desktop()