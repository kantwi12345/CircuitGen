from ansys.aedt.core import Hfss

print("Starting HFSS...")

hfss = Hfss(
    new_desktop=True,
    non_graphical=False
)

print("HFSS connected")