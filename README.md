# Yamaha XMAX 250 — CAN bus decoding (help wanted)

Hobby project: reverse-engineering the CAN traffic on a **Yamaha XMAX 250 (2023)** to build a live dashboard and, later, rider features (emergency-brake hazard flash, remote start, selectable fuel maps).

> This repo and write-up were prepared with the help of an AI assistant (Claude). Data and measurements are real; the decoding is ours and may be wrong — corrections very welcome.

## Setup

- ESP32 + CAN transceiver (TWAI, 500 kbit/s) on the **diagnostic connector**.
- Visible traffic: **0x401 and 0x750–0x774** (38 IDs, ~750 frames/s total), plus ECU replies on 0x7E8 to our own queries (OBD-II Mode 01 and KWP2000 `0x21` local IDs).
- ESP32 streams every frame over BLE to an Android phone, which writes a binary log. Logs here are **lossless** (sequence numbers checked).

## Decoded so far

Fields are little-endian 16-bit words (`w0 = b0 | b1<<8`, `w1 = b2 | b3<<8`, …). Correlation against ECU OBD values over ~20 000 samples / 9.5 km:

| ID | Field | Meaning | Rate | Check |
|---|---|---|---|---|
| 0x750 | `w0 & 0x1FFF` | **Engine RPM** (direct rpm; bit 13 = flag) | 100 Hz | matches OBD rpm |
| 0x758 | `w0 / 10` | **Vehicle speed km/h** (moves in 1 mph = 1.6 km/h steps) | 20 Hz | r = 1.000 |
| 0x758 | `b4` | 01 = engine running | | |
| 0x758 | `b7 & 0x0F` | rolling counter (decrementing) | | |
| 0x764 / 0x756 | `w0 & 0x3FF` | throttle opening | 20 Hz | r = 0.98 |
| 0x768 | `w0 & 0xFFF` | injection time / load | 20 Hz | r = 0.96 |
| 0x753 | `w0 & 0x1FF` | ignition advance | 20 Hz | r = 0.97 |
| 0x752 | `w2 & 0x3FF` | O2 sensor | 20 Hz | r = 0.95 |

Other notes:
- **Coolant and intake air temperature are NOT in the broadcast** (only via ECU query).
- `0x758 w1` looks speed-like but is very noisy — not a clean second wheel speed.
- Odometer is not in the broadcast. The ECU keeps its own distance counter (KWP local ID `0x48`, 0.1 km units), which reads ~2.2 % lower than the dashboard odometer.
- ECU fuel trims read STFT ≈ +11…13 %, LTFT ≈ +7.8 % (if our decoding is right).

## Open questions — any help appreciated

1. Has anyone mapped Yamaha's 0x750–0x774 stream (on XMAX, NMAX, TMAX, MT, R-series…)? Is it the ECU's "monitor" stream?
2. Where are **brake, turn signal, headlight, side-stand switches** and **ABS / TCS intervention** flags? Not obvious in 0x750–0x774.
3. Is there a **second bus** (meter / smart key / ABS) that is not exposed on the diagnostic connector?
4. Experience reading/flashing this ECU (e.g. Woolich) or with multiple fuel maps on small Yamaha scooters?

## Files

- `logs/can_*.bin` — two real sessions (58 s and 8 min, 0–93 km/h).
- `tools/canbin.py` — decode a `.bin`, report frame loss, optionally dump text.
- `tools/load.py` — convert logs to NumPy `.npz` (per-ID frames + ECU JSON values).
- `tools/corr3.py`, `tools/fit.py`, `tools/ride.py` — field search, linear fits, ride stats.

```
cd logs
python ../tools/canbin.py can_20261011_225641.bin
python ../tools/load.py .
python ../tools/ride.py
```

### Binary log format

Records: `type u8 ('R' raw / 'J' JSON)`, `len u16 LE`, `phone_ms u64 LE`, payload.
`R` payload: `seq u32` then N × 14 bytes: `esp_ms u32`, `id11 | dlc<<11 u16`, `data[8]`.
`J` payload: chunks of newline-separated JSON with ECU values (rpm, speed, coolant, throttle, load, map, iat, inj, adv, o2, stft, ltft, …).

Please open an **issue** or **discussion** if you recognise any of these IDs.
