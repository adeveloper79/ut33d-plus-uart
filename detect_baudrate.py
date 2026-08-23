#!/usr/bin/env python3
"""
Baud rate scanner for serial devices and multimeter UART interfaces.
"""
import time
import sys
import glob
import serial
from serial.tools import list_ports

BAUD_RATES = [1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200]

def get_serial_ports():
    ports = [p.device for p in list_ports.comports()]
    if not ports:
        ports = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')
    return sorted(list(set(ports)))

def scan_port(port_name, timeout_per_baud=2.5):
    print(f"\n==========================================")
    print(f" Scanning Serial Port: {port_name}")
    print(f"==========================================")
    found_any = False
    
    for baud in BAUD_RATES:
        print(f"[*] Testing {baud} baud (listening for {timeout_per_baud}s)...", end="", flush=True)
        try:
            with serial.Serial(port_name, baudrate=baud, timeout=0.1) as ser:
                ser.reset_input_buffer()
                start_time = time.time()
                data = bytearray()
                while time.time() - start_time < timeout_per_baud:
                    chunk = ser.read(64)
                    if chunk:
                        data.extend(chunk)
                        
                if data:
                    found_any = True
                    hex_str = " ".join(f"{b:02X}" for b in data[:32])
                    ascii_str = "".join(chr(b) if 32 <= b <= 126 else "." for b in data[:32])
                    print(f" -> RECEIVED {len(data)} BYTES!")
                    print(f"    HEX  : {hex_str}{'...' if len(data) > 32 else ''}")
                    print(f"    ASCII: {ascii_str}{'...' if len(data) > 32 else ''}")
                else:
                    print(" No data.")
        except Exception as e:
            print(f" Error: {e}")
            
    if not found_any:
        print("\n[!] No serial data received at any standard baud rate.")

def main():
    ports = get_serial_ports()
    if not ports:
        print("[!] No USB serial adapter detected (/dev/ttyUSB* or /dev/ttyACM*).")
        sys.exit(1)
        
    port = sys.argv[1] if len(sys.argv) > 1 else ports[0]
    scan_port(port)

if __name__ == "__main__":
    main()
