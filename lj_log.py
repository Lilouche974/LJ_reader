# Real-Time AIN Monitor: LabJack T7
# Reads and plots AIN0 and AIN1 magnitudes + their difference in real time.

import time
import numpy as np
import matplotlib.pyplot as plt
from labjack import ljm

# ====== Config ======
SAMPLING_INTERVAL = 0.2  # seconds (5 Hz)
PLOT_WINDOW = 60         # seconds of data to display
Y_MIN, Y_MAX = -0.5, 3.0  # fixed voltage display range
# =====================

# --- Initialize LabJack ---
handle = ljm.openS("T7", "ANY", "ANY")
info = ljm.getHandleInfo(handle)
print(f"\nConnected to LabJack T7 | Serial: {info[2]}, IP: {ljm.numberToIP(info[3])}\n")

# Configure AIN0 and AIN1 for single-ended ±10V
ain_settings = ["AIN0_RANGE", "AIN0_RESOLUTION_INDEX",
                "AIN1_RANGE", "AIN1_RESOLUTION_INDEX",
                "AIN0_NEGATIVE_CH", "AIN1_NEGATIVE_CH"]
ain_values = [10.0, 0, 10.0, 0, 199, 199]
ljm.eWriteNames(handle, len(ain_settings), ain_settings, ain_values)
print("AIN0 and AIN1 configured.\n")

# --- Initialize Plot ---
plt.ion()
fig, ax = plt.subplots()
fig.canvas.manager.set_window_title("LabJack T7 Real-Time AIN Monitor")
ax.set_xlabel("Time (s)")
ax.set_ylabel("Voltage (V)")
ax.set_title("Real-Time Analog Inputs", fontsize=14)
ax.grid(True)

line1, = ax.plot([], [], label="|AIN0|", lw=2)
line2, = ax.plot([], [], label="|AIN1|", lw=2)
line3, = ax.plot([], [], label="|AIN0 - AIN1|", lw=2, linestyle="--")
ax.legend(loc='upper left')

# --- Data Buffers ---
time_data = []
ain0_data = []
ain1_data = []
diff_data = []
start_time = time.time()

try:
    while True:
        # Read AIN0 and AIN1
        ain0, ain1 = ljm.eReadNames(handle, 2, ["AIN0", "AIN1"])
        now = time.time() - start_time

        # Append data
        time_data.append(now)
        ain0_data.append(abs(ain0))
        ain1_data.append(abs(ain1))
        diff_data.append(abs(ain0 - ain1))

        # Trim old data
        while time_data and (now - time_data[0]) > PLOT_WINDOW:
            time_data.pop(0)
            ain0_data.pop(0)
            ain1_data.pop(0)
            diff_data.pop(0)

        # Update plot
        line1.set_data(time_data, ain0_data)
        line2.set_data(time_data, ain1_data)
        line3.set_data(time_data, diff_data)
        ax.set_xlim(max(0, now - PLOT_WINDOW), now)
        ax.set_ylim(Y_MIN, Y_MAX)

        plt.pause(0.01)
        time.sleep(SAMPLING_INTERVAL)

except KeyboardInterrupt:
    print("\nStopped by user.")

finally:
    ljm.close(handle)
    plt.ioff()
    plt.show()
    print("LabJack handle closed.")
