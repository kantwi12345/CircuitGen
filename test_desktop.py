# test_desktop.py

from ansys.aedt.core import Desktop

Desktop(
    specified_version="2022.1",
    new_desktop=True,
    non_graphical=False
)

print("Connected")