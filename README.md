TODO

- put Rfb1, Rfb2, Rt labels
- c6 footprint?
- order 1uf, 2.2nF, Rt

![3D rendering](pcb3d.webp)

## Specs
|      |   |         |
|------|---|---------|
| Vin  | 6 | 100     |
| Vout |   | 20      |
| Iout |   | 0.5     |
| fsw  |   | 1000khz |

## LM516x features

* [LM5163](https://www.ti.com/lit/ds/symlink/lm5163.pdf) (.5A) LM5164](https://www.ti.com/lit/ds/symlink/lm5164.pdf) (
  1A)
* sync buck with nearly 100% max duty cycle
* 0.725Ω NFET buck switch, 0.34Ω NFET synchronous rectifier
* constant on-time (COT) control architecture
* light-load power saving mode
* 10.5µA no-load input quiescent current
* soft-start, UVLO, thermal shutdown
* PGOOD indicator
* quick start calc: https://www.ti.com/tool/LM5163-LM5164DESIGN-CALC

![Ripple Generation Methods](ripple-gen.webp)

## Ti Design Tool

* WEBENCH Power
  Designer https://webench.ti.com/power-designer/switching-regulator?base_pn=LM5163&origin=ODS&litsection=features
* LM218x Excel Tool

# Pin-compatible chips

| MPN     | Vi  | Io   | NFET Rds  | Iq   |                  | Light-Load |                                                               |
|---------|-----|------|-----------|------|------------------|------------|---------------------------------------------------------------|
| LM5168  | 120 | 0.3  | 1.9/.71Ω  | 10µA | COT, FPWM or PFM | DEM        | [pdf](https://www.ti.com/lit/ds/symlink/lm5169.pdf)           |
| LM5169  | 120 | 0.65 | 1.9/.71Ω  | 10µA | COT, FPWM or PFM | DEM        | [pdf](https://www.ti.com/lit/ds/symlink/lm5169.pdf)           |
| LM5163  | 100 | 0.5  | .725/.34Ω | 10µA | COT              | DEM        | https://www.ti.com/lit/ds/symlink/lm5163.pdf?ts=1731081870545 |
| LM5164  | 100 | 1.0  | .725/.34Ω | 10µA | COT              | DEM        | https://www.ti.com/lit/ds/symlink/lm5163.pdf?ts=1731081870545 |
| LM5017  | 100 | 0.6  |           |      | COT              |            |                                                               |
| LM34927 |     |      |           |      |                  |            |                                                               |

https://webench.ti.com/power-designer/switching-regulator/select

#                        

## Feedback Resistor Values  
                      
| Vout |      | Rfb1 | Rfb2 | f_sw | Rt | Ra@100khz                | L     |
|------|------|------|------|------|----|--------------------------|-------|
| 3.33 |      | 390k | 220k |      |    | 715k                     | 400uh | 
| 3.35 |      | 430k | 240k |      |    |                          |       |
| 11.2 |      | 470k | 56k  |      |    | 1.5k                     |       |
| 11.3 |      | 430k | 51k  |      |    | 1.5k                     |       |
| 11.3 |      | 430k | 50k  |      |    | 600..1.4k   WR08X155 JTL |       |


[Common Resistor Values](https://ch00ftech.com/wp-content/uploads/2012/05/resistorsandcaps.pdf)


## inductors

requirements:

* Isat well above current limit setting
* Isat decreases with rising temperature
* refer to datasheet [pg 18](https://www.ti.com/lit/ds/symlink/lm5163.pdf#page=18)

|                      | L     | Isat(30%) | DCRmΩ(max) | Q         | px(250) | size | Notes                                                                                           |
|----------------------|-------|-----------|------------|-----------|---------|------|-------------------------------------------------------------------------------------------------|
| MSS1260-124KL        | 120uH | 2A        | 195        |           | 1,33€   | 12mm | LM5163 datasheet                                                                                |
| Bourns SRN6045-101M  | 100uH | .7A       | 494        | 22@796kHz | $,27    | 6mm  |                                                                                                 |
| VLS5045EX-101M       | 100uH | .7A       | 754        |           | $,20    | 5mm  | ordered                                                                                         |
| → TY NRS8040T101MJGK | 100uH | 1.1A      | 364        |           | $,22    | 8mm  | [pdf](https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/2544/NRS8040T101MJGK_SS.pdf) |
| IFSC3232DBER471M02   |       |           |            |           |         |      |                                                                                                 |
|                      |       |           |            |           |         |      |                                                                                                 |

## Other designs using same chip

* https://github.com/90wishpack/LM5164
* https://github.com/FarwayDot/Adapter_PowerSupply_Vigi