# UNI-T UT33D+ Multimeter UART Reverse Engineering & Live Decoder

Hardware mod, protocol documentation, and Python tools for reading live measurement streams from the **UNI-T UT33D+** digital multimeter via its internal PCB UART test pads.

---

## 🛠️ Hardware & Pinout

The UT33D+ PCB features factory test pads connected directly to the internal Chip-on-Board (COB) microcontroller UART transmitter.

### Wiring:
| UT33D+ PCB Pad | USB-to-TTL Adapter | Notes |
| :--- | :--- | :--- |
| **TXD** | **RXD** | Multimeter serial output line |
| **GND** | **GND** | Common reference ground |

> [!IMPORTANT]
> **Logic Level**: The UT33D+ runs on $2\times\text{AAA}$ batteries ($\approx 3\text{V}$). Always configure your USB-to-TTL converter (e.g. CH340, CP2102, FTDI) to **3.3V logic** (do not apply 5V TTL).

---

## ⚡ Serial UART Specifications

* **Baud Rate**: `2400`
* **Data Bits**: `8`
* **Parity**: `None` (`N`)
* **Stop Bits**: `1`
* **Flow Control**: `None`
* **Frame Rate**: Continuous stream ($\approx 3\text{ packets/sec}$)

---

## 📦 Packet Structure

Each packet consists of a fixed **10-byte frame**:

```
 0    1    2    3    4    5    6    7    8    9
[AB] [CD] [01] [RR] [SS] [SS] [VV] [VV] [FF] [CC]
 |    |    |    |   \--------v--------/   |    |
 +----+    |    |      32-bit signed      |    +-- Trailer / Checksum
 Header    |    |     count (Big Endian)  +------- Flags (0x03 negative, 0x00 positive)
           |    +--------------------------------- Range Code (Dial Position)
           +-------------------------------------- Mode Byte (0x01)
```

### Field Breakdown:
1. **`0xAB 0xCD` (Bytes 0–1)**: Synchronization header.
2. **`0x01` (Byte 2)**: Measurement category identifier.
3. **`RR` (Byte 3)**: Active rotary switch dial / range code (see table below).
4. **`Bytes 4–7`**: **32-bit Signed Big-Endian Integer** (`int.from_bytes(pkt[4:8], 'big', signed=True)`).
   * **Positive voltages**: `0x00 0x00 0x01 0x38` $\rightarrow +312$ counts ($+3.12\text{ V}$).
   * **Negative voltages**: `0xFF 0xFF 0xFE 0x82` $\rightarrow -382$ counts ($-3.82\text{ V}$).
5. **`FF` (Byte 8)**: Status flags (`0x03` on negative polarity, `0x00` on positive).
6. **`CC` (Byte 9)**: Trailer / Checksum byte.

---

## 🧭 Complete Rotary Dial & Range Table

| Range Byte (Hex) | Multimeter Function | Multiplier / Scale | Formatted Display |
| :--- | :--- | :--- | :--- |
| **`0x16`** | **200mV DC** | $\times 0.1\text{ mV}$ | `±XXX.X mV` |
| **`0x14`** | **2000mV DC** | $\times 1.0\text{ mV}$ | `±XXXX mV` |
| **`0x15`** | **20V DC** | $\times 0.01\text{ V}$ | `±XX.XX V` |
| **`0x11`** | **200V DC** | $\times 0.1\text{ V}$ | `±XXX.X V` |
| **`0x13`** | **600V DC** | $\times 1.0\text{ V}$ | `±XXX V` |
| **`0x1A`** | **200V AC** | $\times 0.1\text{ V}$ | `XXX.X V` |
| **`0x12`** | **600V AC** | $\times 1.0\text{ V}$ | `XXX V` |
| **`0x1F`** | **2000µA DC** | $\times 1.0\ \mu\text{A}$ | `±XXXX µA` |
| **`0x1E`** | **20mA DC** | $\times 0.01\text{ mA}$ | `±XX.XX mA` |
| **`0x17`** | **200mA DC** | $\times 0.1\text{ mA}$ | `±XXX.X mA` |
| **`0x1C`** | **10A DC** | $\times 0.01\text{ A}$ | `±XX.XX A` |
| **`0x1D`** | **200Ω** | $\times 0.1\ \Omega$ | `XXX.X Ω` |
| **`0x0D`** | **2000Ω** | $\times 1.0\ \Omega$ | `XXXX Ω` |
| **`0x0F`** | **20kΩ** | $\times 0.01\text{ k}\Omega$ | `XX.XX kΩ` |
| **`0x0E`** | **200kΩ** | $\times 0.1\text{ k}\Omega$ | `XXX.X kΩ` |
| **`0x0B`** | **20MΩ** | $\times 0.01\text{ M}\Omega$ | `XX.XX MΩ` |
| **`0x07`** | **200MΩ** | $\times 0.1\text{ M}\Omega$ | `XXX.X MΩ` |
| **`0x1B`** | **Diode / Continuity** | $\times 0.001\text{ V}$ | `X.XXX V` / `O.L` |
| **`0x19`** | **NCV** | — | Non-contact voltage detection |

---

## 🚀 Quickstart & Usage

### 1. Requirements
```bash
pip install -r requirements.txt
```

### 2. Live Reading CLI
Stream live decoded measurements with automatic port detection:
```bash
python3 ut33d_read.py
```
Or specify the port explicitly:
```bash
python3 ut33d_read.py /dev/ttyUSB0
```

#### Example Output:
```
========================================================================
 UNI-T UT33D+ Digital Multimeter Real-time Reader
========================================================================
Time       | Range    | Dial Function    | Reading          | Raw Packet
------------------------------------------------------------------------
16:58:16   | 0x15     | 20V DC           | +3.12 V          | AB CD 01 15 00 00 01 38 00 50
16:58:20   | 0x15     | 20V DC           | -3.82 V          | AB CD 01 15 FF FF FE 82 03 94
16:58:30   | 0x0B     | 20MΩ             | O.L MΩ           | AB CD 01 0B 00 00 08 B5 00 CA
```

### 3. Diagnostic & Calibration Tools
* **`detect_baudrate.py`**: Scans serial speeds from 1200 to 115200 baud.
* **`ut33d_monitor.py`**: Hex dump and raw frame monitor.
* **`map_modes.py`**: Interactive dial position discovery and calibration script.

---

## 🐍 Python Integration Example

```python
import serial
from ut33d_read import decode_reading

with serial.Serial('/dev/ttyUSB0', baudrate=2400, timeout=1.0) as ser:
    while True:
        if ser.read(1) == b'\xAB' and ser.read(1) == b'\xCD':
            pkt = b'\xAB\xCD' + ser.read(8)
            fn_name, raw_val, reading_str, range_code = decode_reading(pkt)
            print(f"[{fn_name}] -> {reading_str}")
```

---

## 📄 License
MIT
