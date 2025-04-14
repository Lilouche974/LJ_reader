# LabJack T7 Real-Time Analog Input Reader
# This script reads analog inputs AIN0 and AIN1 from a LabJack T7 device
# Plots the absolute values of AIN0 and AIN1 in real-time

import time
import numpy as np
import matplotlib.pyplot as plt
from labjack import ljm

# Open first found LabJack
handle = ljm.openS("T7", "ANY", "ANY")  # Ensure it's a T7 device

# Get device info
info = ljm.getHandleInfo(handle)
print("\nOpened a LabJack with Device type: %i, Connection type: %i,\n"
      "Serial number: %i, IP address: %s, Port: %i,\nMax bytes per MB: %i" %
      (info[0], info[1], info[2], ljm.numberToIP(info[3]), info[4], info[5]))

# Configure AIN0 and AIN1
aNames = ["AIN0_RANGE", "AIN0_RESOLUTION_INDEX",
          "AIN1_RANGE", "AIN1_RESOLUTION_INDEX",
          "AIN0_NEGATIVE_CH", "AIN1_NEGATIVE_CH"]
aValues = [10.0, 0, 10.0, 0, 199, 199]  # +/-10V range, single-ended
ljm.eWriteNames(handle, len(aNames), aNames, aValues)

print("\nConfiguration set for AIN0 and AIN1.")

# Initialize plot
plt.ion()
fig, ax = plt.subplots()
time_data = []
ain0_data = []
ain1_data = []
difference_data = []

line1, = ax.plot([], [], label="AIN0 Magnitude (V)")
line2, = ax.plot([], [], label="AIN1 Magnitude (V)")
line3, = ax.plot([], [], label="|AIN0 - AIN1| (V)")
ax.set_xlim(0, 10)  # Initial x-axis range
ax.set_ylim(0, 10)  # Initial y-axis range
ax.set_xlabel("Time (s)")
ax.set_ylabel("Voltage (V)")
ax.legend()
plt.title("Real-Time Analog Input Magnitudes")

start_time = time.time()
sampling_interval = 0.2  # 5 Hz (200 ms)

try:
    while True:
        # Read AIN0 and AIN1
        results = ljm.eReadNames(handle, 2, ["AIN0", "AIN1"])
        ain0 = abs(results[0])
        ain1 = abs(results[1])
        difference = abs(ain0 - ain1)

        # Update data
        current_time = time.time() - start_time
        time_data.append(current_time)
        ain0_data.append(ain0)
        ain1_data.append(ain1)
        difference_data.append(difference)

        # Update plot
        line1.set_data(time_data, ain0_data)
        line2.set_data(time_data, ain1_data)
        line3.set_data(time_data, difference_data)
        ax.set_xlim(0, max(10, current_time))  # Dynamically adjust x-axis
        ax.set_ylim(2.75, max(2.9, max(ain0_data + ain1_data + difference_data)))  # Adjust y-axis

        plt.pause(0.01)  # Pause to update the plot
        time.sleep(sampling_interval)  # Maintain 5 Hz sampling rate

except KeyboardInterrupt:
    print("\nExperiment stopped by user.")

finally:
    # Close LabJack handle
    ljm.close(handle)
    print("LabJack handle closed.")