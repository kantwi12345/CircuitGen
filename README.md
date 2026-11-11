@"

\# CircuitGen



CircuitGen is a Python-based HFSS automation platform that generates antenna geometries automatically in Ansys Electronics Desktop (HFSS) using the PyWin32 COM interface.



The goal of CircuitGen is to provide a programmable antenna generation pipeline that can create, modify, simulate, and optimize antenna designs directly from an API.



\---



\# Features



\## HFSS Automation



\- Automatic HFSS project creation

\- Automatic design creation

\- Automatic geometry generation

\- Automatic radiation boundary creation

\- Automatic air region generation

\- FastAPI integration

\- Swagger UI support



\---



\# Supported Antennas



\## Patch Antenna



Currently supports:



\- FR4 substrate

\- Ground plane

\- Patch radiator

\- Feed line

\- Lumped port sheet

\- Air box



\---



\## Monopole Antenna



Currently supports:



\- Ground plane

\- Monopole radiator

\- Feed geometry

\- Port sheet

\- Air box



\---



\## Dipole Antenna



Currently supports:



\- Cylindrical dipole

\- Center feed gap

\- Embedded port sheet

\- Air box



\---



\## Yagi-Uda Antenna (Prototype)



Current implementation includes:



\- Reflector

\- Driven element

\- Feed gap

\- Port sheet

\- Three directors

\- Boom

\- Feed cone

\- Air box

\- Radiation boundary



Note:



The Yagi implementation is currently a prototype and uses provisional engineering dimensions.



\---



\# Technology Stack



\## Backend



\- Python 3.9+

\- FastAPI

\- Pydantic

\- Uvicorn



\## HFSS Interface



\- PyWin32

\- COM Automation

\- Ansys Electronics Desktop

\- HFSS



\---



\# Project Structure



```text

CircuitGen

│

├── backend

│   └── app.py

│

├── tools

│   └── hfss\_com.py

│

├── exports

├── reports

├── results

│

├── README.md

├── .gitignore

└── requirements.txt

