CircuitGen - ADS Workspace
=========================

Design      : Impedance Matching Network
Netlist     : Impedance_Matching_Network.net

Steps to simulate in ADS:
-------------------------
1. Open ADS (the build command already launches it).
2. Open the workspace folder that contains this file.
3. Import the netlist:
   File > Import > SPICE Netlist... > Impedance_Matching_Network.net
4. Place the imported components on the schematic and connect
   per the node names in the netlist.
5. Add a port at the input and at the load node, then set up
   the simulation (S-parameter / harmonic balance).
6. Verify the design targets listed in the netlist header.

Note: excitation, ports and sweeps are configured manually in ADS
      (same approach as the HFSS geometry-only workflow).
