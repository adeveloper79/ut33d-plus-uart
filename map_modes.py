#!/usr/bin/env python3
"""
Interactive calibration tool to map new dial positions and functions.
"""
import time
import sys
import json
import serial

def main():
    port = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyUSB0"
    print(f"Connecting to {port} @ 2400 baud...")
    ser = serial.Serial(port, baudrate=2400, timeout=1.0)
    ser.reset_input_buffer()
    
    print("\n=======================================================")
    print(" UT33D+ DIAL MODE MAPPER")
    print(" Rotate the dial through every position to log new range codes.")
    print("=======================================================\n")
    
    known_modes = {}
    last_combo = None
    
    try:
        while True:
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
            b2 = pkt[2]
            b3 = pkt[3]
            raw_val = int.from_bytes(pkt[4:8], byteorder='big', signed=True)
            combo_key = f"0x{b2:02X}_0x{b3:02X}"
            
            if combo_key != last_combo:
                last_combo = combo_key
                raw_hex = " ".join(f"{b:02X}" for b in pkt)
                if combo_key not in known_modes:
                    known_modes[combo_key] = {
                        "mode_byte": f"0x{b2:02X}",
                        "range_byte": f"0x{b3:02X}",
                        "sample_packet": raw_hex,
                        "sample_raw_val": raw_val
                    }
                    print(f"\n[+] NEW MODE DETECTED: Mode=0x{b2:02X}, Range=0x{b3:02X}")
                    print(f"    Sample Packet : {raw_hex}")
                    print(f"    Raw Value Count: {raw_val}")
                    print(f"    Total Modes Mapped: {len(known_modes)}")
                else:
                    print(f"\n[->] Dial switched to: Mode=0x{b2:02X}, Range=0x{b3:02X} (Raw: {raw_val})")
                    
            time.sleep(0.05)
            
    except KeyboardInterrupt:
        print("\nExiting mapper...")
    finally:
        ser.close()

if __name__ == "__main__":
    main()
