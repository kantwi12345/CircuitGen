# ADS Schematic Build Sheet - LNA

Follow the ADS 2023 schematic creation flow below and place the
parts listed in the tables.

## 1. New schematic

| Field | Value |
|---|---|
| Action | File > New > Schematic (or the New Schematic toolbar icon) |
| Library | `LNA_lib` (local design library) |
| Cell Name | `lna` (no spaces) |

## 2. Palette

Use the Palette drop-down in the schematic window (top left):

| Part type used | Palette | Palette item |
|---|---|---|
| V | Sources | DC Voltage Source / Vtone |
| R | Lumped-Components | Resistor |
| C | Lumped-Components | Capacitor |
| L | Lumped-Components | Inductor |
| G | Sources | Voltage Controlled Current Source |

## 3. Parts and values

Click the parameter text next to a placed part (e.g. `R=50 Ohm`) and
type the value below. Press Ctrl+R before or after clicking to
rotate a part by 90 degrees, Esc to exit placement mode.

| RefDes | Type | Value | Palette item |
|---|---|---|---|
| VTH | V | `DC 0.0 / AC 1.0` | Sources / DC Voltage Source / Vtone |
| VCC | V | `DC 3.3 / AC 0.0` | Sources / DC Voltage Source / Vtone |
| RSRC | R | `50 Ohm` | Lumped-Components / Resistor |
| CPAD | C | `9.5 pF` | Lumped-Components / Capacitor |
| LSIG | L | `856 nH` | Lumped-Components / Inductor |
| RB | R | `20 Ohm` | Lumped-Components / Resistor |
| RPI | R | `2.068 kOhm` | Lumped-Components / Resistor |
| CPI | C | `15 pF` | Lumped-Components / Capacitor |
| GM | G | `gain = 0.058` | Sources / Voltage Controlled Current Source |
| RO | R | `30 kOhm` | Lumped-Components / Resistor |
| RE | R | `330 Ohm` | Lumped-Components / Resistor |
| CE | C | `10 uF` | Lumped-Components / Capacitor |
| RB1 | R | `16 kOhm` | Lumped-Components / Resistor |
| RB2 | R | `11 kOhm` | Lumped-Components / Resistor |
| CO1 | C | `9.7 pF` | Lumped-Components / Capacitor |
| LOUT | L | `544 nH` | Lumped-Components / Inductor |
| CO2 | C | `49.3 pF` | Lumped-Components / Capacitor |
| RL | R | `50 Ohm` | Lumped-Components / Resistor |
| CDP | C | `10000 nF` | Lumped-Components / Capacitor |
| CHP | C | `10000 nF` | Lumped-Components / Capacitor |

## 4. Wiring (Ctrl+W)

Start the wire on a red pin and end it on the pin of the next part.
Every connection below must exist in the schematic.

| Net | Pins |
|---|---|
| GND | CDP.-, CE.-, CHP.-, CO1.-, CO2.-, CPAD.-, RB2.-, RE.-, RL.-, VCC.-, VTH.- |
| BINT | CPI.+, GM.c+, RB.+, RPI.+ |
| NC | CO1.+, GM.+, LOUT.+, RO.+ |
| NE | CE.+, CPI.-, GM.c-, GM.c-, RE.+, RO.-, RPI.- |
| NI | LSIG.-, RB.-, RB1.+, RB2.+ |
| NO2 | CO2.+, LOUT.-, RL.+ |
| SRC | RSRC.+, VTH.+ |
| SRC1 | CPAD.+, LSIG.+, RSRC.- |
| VCC | CDP.+, CHP.+, RB1.-, VCC.+ |

## 5. Ground

Click the Insert Ground icon (triangle) on the top toolbar and place
a ground on the GND net.

| Net | Pins requiring ground |
|---|---|
| 0 | CDP.-, CE.-, CHP.-, CO1.-, CO2.-, CPAD.-, RB2.-, RE.-, RL.-, VCC.-, VTH.- |

## 6. Save

File > Save (Ctrl+S) to save the schematic cell in the local library.

Layout units for this workspace: **mm**

## 7. Simulation setup (after the schematic is saved)

1. Simulation > Setup Simulation / New Simulation > S-Parameter.
2. Add ports: TermG at the input net and at the output/load net.
3. Sweep the frequency range around the design frequency.
4. Run the analysis and review S11 / S21 / power.

Note: the matching network netlist is also stored in the library
netlists folder and can be imported if you prefer to start from it.
