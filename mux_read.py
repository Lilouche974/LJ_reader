# Real-Time AIN Monitor: LabJack T7 with MUX80
# Scans through all possible AIN channels and displays live voltage readings.

import time
import numpy as np
import matplotlib.pyplot as plt
from labjack import ljm

# ====== Config ======
SAMPLING_INTERVAL = 0.25  # seconds (4 Hz)
MUX_CHANNELS = 120        # Total AIN channels with MUX80
Y_MIN, Y_MAX = -10.0, 10.0  # Voltage range for display
# =====================

# --- Initialize LabJack ---
handle = ljm.openS("T7", "ANY", "ANY")
info = ljm.getHandleInfo(handle)
print(f"\nConnected to LabJack T7 | Serial: {info[2]}, IP: {ljm.numberToIP(info[3])}\n")

# Configure all AIN channels for single-ended ±10V
ain_settings = []
ain_values = []
for i in range(MUX_CHANNELS):
    ain_settings.append(f"AIN{i}_RANGE")
    ain_values.append(10.0)  # ±10V range
ljm.eWriteNames(handle, len(ain_settings), ain_settings, ain_values)
print(f"Configured {MUX_CHANNELS} AIN channels for ±10V range.\n")

# --- Initialize Plot ---
plt.ion()
fig, ax = plt.subplots(figsize=(12, 8))
fig.canvas.manager.set_window_title("LabJack T7 Real-Time AIN Monitor")
ax.set_xlabel("AIN Channel")
ax.set_ylabel("Voltage (V)")
ax.set_title("Real-Time Analog Input Voltages", fontsize=14)
ax.set_ylim(Y_MIN, Y_MAX)
ax.grid(True)

bars = ax.bar(range(MUX_CHANNELS), [0] * MUX_CHANNELS, tick_label=[f"AIN{i}" for i in range(MUX_CHANNELS)])
plt.xticks(rotation=90)
plt.tight_layout()

try:
    while True:
        # Read all AIN channels
        ain_names = [f"AIN{i}" for i in range(MUX_CHANNELS)]
        voltages = ljm.eReadNames(handle, MUX_CHANNELS, ain_names)

        # Update bar heights
        for bar, voltage in zip(bars, voltages):
            bar.set_height(voltage)

        # Redraw plot
        plt.pause(0.01)
        time.sleep(SAMPLING_INTERVAL)

except KeyboardInterrupt:
    print("\nStopped by user.")

finally:
    ljm.close(handle)
    plt.ioff()
    plt.show()
    print("LabJack handle closed.")
