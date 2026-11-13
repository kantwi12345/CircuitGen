# ADS Schematic Build Sheet - Class AB Audio Power Amplifier

Follow the ADS 2023 schematic creation flow below and place the
parts listed in the tables.

## 1. New schematic

| Field | Value |
|---|---|
| Action | File > New > Schematic (or the New Schematic toolbar icon) |
| Library | `Class_AB_Audio_Power_Amplifier_lib` (local design library) |
| Cell Name | `class_ab_audio_power_amplifier` (no spaces) |

## 2. Palette

Use the Palette drop-down in the schematic window (top left):

| Part type used | Palette | Palette item |
|---|---|---|
| V | Sources | DC Voltage Source / Vtone |
| R | Lumped-Components | Resistor |
| C | Lumped-Components | Capacitor |
| E | Sources | Voltage Controlled Voltage Source |

## 3. Parts and values

Click the parameter text next to a placed part (e.g. `R=50 Ohm`) and
type the value below. Press Ctrl+R before or after clicking to
rotate a part by 90 degrees, Esc to exit placement mode.

| RefDes | Type | Value | Palette item |
|---|---|---|---|
| VPOS | V | `DC 35.0 / AC 0.0` | Sources / DC Voltage Source / Vtone |
| VNEG | V | `DC -35.0 / AC 0.0` | Sources / DC Voltage Source / Vtone |
| VIN | V | `DC 0.0 / AC 1.0` | Sources / DC Voltage Source / Vtone |
| RSRC | R | `50 Ohm` | Lumped-Components / Resistor |
| CIN | C | `10000 nF` | Lumped-Components / Capacitor |
| RI | R | `1 kOhm` | Lumped-Components / Resistor |
| RF | R | `100 kOhm` | Lumped-Components / Resistor |
| CG | C | `10000 nF` | Lumped-Components / Capacitor |
| EOUT | E | `gain = 1.0` | Sources / Voltage Controlled Voltage Source |
| RL | R | `8 Ohm` | Lumped-Components / Resistor |
| RZ | R | `0 Ohm` | Lumped-Components / Resistor |
| CZO | C | `1000 nF` | Lumped-Components / Capacitor |
| CDP | C | `220 uF` | Lumped-Components / Capacitor |
| CHP | C | `10000 nF` | Lumped-Components / Capacitor |
| CDN | C | `220 uF` | Lumped-Components / Capacitor |
| CHN | C | `10000 nF` | Lumped-Components / Capacitor |

## 4. Wiring (Ctrl+W)

Start the wire on a red pin and end it on the pin of the next part.
Every connection below must exist in the schematic.

| Net | Pins |
|---|---|
| GND | CDN.-, CDP.-, CG.-, CHN.-, CHP.-, CZO.-, EOUT.c-, EOUT.c-, RL.-, VIN.-, VNEG.-, VPOS.- |
| IN | RSRC.+, VIN.+ |
| IN1 | CIN.+, RSRC.- |
| NG | CIN.-, RF.-, RI.+ |
| OFB | CG.+, EOUT.c+, RF.+, RI.- |
| OUT | EOUT.+, RL.+, RZ.- |
| VN | CDN.+, CHN.+, VNEG.+ |
| VP | CDP.+, CHP.+, VPOS.+ |
| ZO | CZO.+, RZ.+ |

## 5. Ground

Click the Insert Ground icon (triangle) on the top toolbar and place
a ground on the GND net.

| Net | Pins requiring ground |
|---|---|
| 0 | CDN.-, CDP.-, CG.-, CHN.-, CHP.-, CZO.-, EOUT.c-, EOUT.c-, RL.-, VIN.-, VNEG.-, VPOS.- |

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
