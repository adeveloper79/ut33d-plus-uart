#!/usr/bin/env python3
"""
UNI-T UT33D+ Digital Multimeter Real-time Data Decoder & CLI Logger
"""

import sys
import time
import serial
from serial.tools import list_ports

RANGE_MAP = {
    # DC Voltage
    0x16: {"name": "200mV DC",     "unit": "mV",  "scale": 0.1,   "signed": True,  "fmt": ".1f"},
    0x14: {"name": "2000mV DC",    "unit": "mV",  "scale": 1.0,   "signed": True,  "fmt": ".0f"},
    0x15: {"name": "20V DC",       "unit": "V",   "scale": 0.01,  "signed": True,  "fmt": ".2f"},
    0x11: {"name": "200V DC",      "unit": "V",   "scale": 0.1,   "signed": True,  "fmt": ".1f"},
    0x13: {"name": "600V DC",      "unit": "V",   "scale": 1.0,   "signed": True,  "fmt": ".0f"},

    # AC Voltage
    0x1A: {"name": "200V AC",      "unit": "V",   "scale": 0.1,   "signed": False, "fmt": ".1f"},
    0x12: {"name": "600V AC",      "unit": "V",   "scale": 1.0,   "signed": False, "fmt": ".0f"},

    # DC Current
    0x1F: {"name": "2000µA DC",    "unit": "µA",  "scale": 1.0,   "signed": True,  "fmt": ".0f"},
    0x1E: {"name": "20mA DC",      "unit": "mA",  "scale": 0.01,  "signed": True,  "fmt": ".2f"},
    0x17: {"name": "200mA DC",     "unit": "mA",  "scale": 0.1,   "signed": True,  "fmt": ".1f"},
    0x1C: {"name": "10A DC",       "unit": "A",   "scale": 0.01,  "signed": True,  "fmt": ".2f"},

    # Resistance
    0x1D: {"name": "200Ω",         "unit": "Ω",   "scale": 0.1,   "signed": False, "fmt": ".1f"},
    0x0D: {"name": "2000Ω",        "unit": "Ω",   "scale": 1.0,   "signed": False, "fmt": ".0f"},
    0x0F: {"name": "20kΩ",         "unit": "kΩ",  "scale": 0.01,  "signed": False, "fmt": ".2f"},
    0x0E: {"name": "200kΩ",        "unit": "kΩ",  "scale": 0.1,   "signed": False, "fmt": ".1f"},
    0x0B: {"name": "20MΩ",         "unit": "MΩ",  "scale": 0.01,  "signed": False, "fmt": ".2f"},
    0x07: {"name": "200MΩ",        "unit": "MΩ",  "scale": 0.1,   "signed": False, "fmt": ".1f"},

    # Diode / Continuity / NCV
    0x1B: {"name": "Diode / Cont", "unit": "V",   "scale": 0.001, "signed": False, "fmt": ".3f"},
    0x19: {"name": "NCV",          "unit": "",    "scale": 1.0,   "signed": False, "fmt": "g"},
}

def decode_reading(pkt):
    range_byte = pkt[3]
    # 32-bit signed integer count across bytes 4..7
    raw_val = int.from_bytes(pkt[4:8], byteorder='big', signed=True)
    
    cfg = RANGE_MAP.get(range_byte, {
        "name": f"Unknown (0x{range_byte:02X})",
        "unit": "",
        "scale": 1.0,
        "signed": True,
        "fmt": "g"
    })
    
    is_negative = raw_val < 0
    abs_count = abs(raw_val)
    
    # Overload condition (usually > 2200 counts on a 2000-count meter)
    if abs_count > 2500:
        val_str = f"{'-' if is_negative else ''}O.L {cfg['unit']}".strip()
    else:
        calc_val = raw_val * cfg["scale"]
        if cfg["signed"]:
            sign_str = "-" if calc_val < 0 else "+"
            val_str = f"{sign_str}{abs(calc_val):{cfg['fmt']}} {cfg['unit']}".strip()
        else:
            val_str = f"{abs(calc_val):{cfg['fmt']}} {cfg['unit']}".strip()
            
    return cfg["name"], raw_val, val_str, range_byte

def auto_detect_port():
    ports = [p.device for p in list_ports.comports() if "USB" in p.device or "ACM" in p.device]
    return ports[0] if ports else "/dev/ttyUSB0"

def main():
    port = sys.argv[1] if len(sys.argv) > 1 else auto_detect_port()
    baud = 2400

    print(f"Connecting to {port} @ {baud} baud (8N1)...")
    try:
        ser = serial.Serial(port, baudrate=baud, timeout=1.0)
    except Exception as e:
        print(f"Error opening port {port}: {e}")
        sys.exit(1)

    ser.reset_input_buffer()
    print("=" * 72)
    print(" UNI-T UT33D+ Digital Multimeter Real-time Reader")
    print("=" * 72)
    print(f"{'Time':<10} | {'Range':<8} | {'Dial Function':<16} | {'Reading':<16} | {'Raw Packet'}")
    print("-" * 72)

    try:
        while True:
            # Sync Header: 0xAB 0xCD
            h1 = ser.read(1)
            if h1 != b'\xAB':
                continue
            h2 = ser.read(1)
            if h2 != b'\xCD':
                continue
                
            payload = ser.read(8)
            if len(payload) < 8:
                continue
                
            pkt = b'\xAB\xCD' + payload
            fn_name, raw_val, reading_str, r_byte = decode_reading(pkt)
            timestamp = time.strftime("%H:%M:%S")
            raw_hex = " ".join(f"{b:02X}" for b in pkt)
            
            print(f"{timestamp:<10} | 0x{r_byte:02X}     | {fn_name:<16} | {reading_str:<16} | {raw_hex}")
            
    except KeyboardInterrupt:
        print("\nDisconnected.")
    finally:
        ser.close()

if __name__ == "__main__":
    main()
