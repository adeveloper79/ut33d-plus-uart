#!/usr/bin/env python3
"""
Raw packet monitor and diagnostic tool for UNI-T UT33D+ serial stream.
"""
import time
import sys
import serial

def listen_dmm(port="/dev/ttyUSB0", baudrate=2400):
    print(f"Connecting to {port} @ {baudrate} baud (8N1)...")
    try:
        ser = serial.Serial(port, baudrate=baudrate, timeout=1.0)
    except Exception as e:
        print(f"Error opening port: {e}")
        return

    ser.reset_input_buffer()
    print("Listening for raw packets (Press Ctrl+C to stop)...")
    print(f"{'Time':<10} | {'Raw Packet (HEX)':<32} | {'Signed 32-bit':<15}")
    print("-" * 62)

    try:
        while True:
            sync = ser.read(1)
            if sync != b'\xab':
                continue
            sync2 = ser.read(1)
            if sync2 != b'\xcd':
                continue

            payload = ser.read(8)
            if len(payload) < 8:
                continue

            packet = b'\xab\xcd' + payload
            hex_repr = " ".join(f"{b:02X}" for b in packet)
            raw_val = int.from_bytes(packet[4:8], byteorder='big', signed=True)
            timestamp = time.strftime("%H:%M:%S")
            print(f"{timestamp:<10} | {hex_repr:<32} | {raw_val:<15}")
            
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        ser.close()

if __name__ == "__main__":
    port = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyUSB0"
    listen_dmm(port)
