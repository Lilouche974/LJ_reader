import time
import numpy as np
import matplotlib.pyplot as plt
import csv
import os
from labjack import ljm


SAMPLING_INTERVAL = 0.25  
MUX_CHANNELS = 120
Y_MIN, Y_MAX = -10.0, 10.0  
TEMP_Y_MIN, TEMP_Y_MAX = -100, 400
CSV_FILENAME = "labjack_data.csv"


a0 = 207.313253
a1 = -126.180277
a2 = -3.928505
a3 = -0.942699
a4 = -0.215084
a5 = -0.074933
a6 = -0.016769
Zl = 0.4969960998
Zu = 1.030625219

def cheb_eq(Zv):
    offset_v = 2.289562
    Zv = Zv - offset_v
    k = ((Zv - Zl) - (Zu - Zv)) / (Zu - Zl)
    acos_k = np.arccos(np.clip(k, -1, 1))
    return (
        a0 * np.cos(0 * acos_k) +
        a1 * np.cos(1 * acos_k) +
        a2 * np.cos(2 * acos_k) +
        a3 * np.cos(3 * acos_k) +
        a4 * np.cos(4 * acos_k) +
        a5 * np.cos(5 * acos_k) +
        a6 * np.cos(6 * acos_k)
    )


handle = ljm.openS("T7", "ANY", "ANY")
info = ljm.getHandleInfo(handle)
print(f"\nConnected to LabJack T7 | Serial: {info[2]}, IP: {ljm.numberToIP(info[3])}\n")


ain_settings = [f"AIN{i}_RANGE" for i in range(MUX_CHANNELS)]
ain_values = [10.0] * MUX_CHANNELS
ljm.eWriteNames(handle, len(ain_settings), ain_settings, ain_values)
print(f"Configured {MUX_CHANNELS} AIN channels for ±10V range.\n")


plt.ion()
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)
fig.canvas.manager.set_window_title("LabJack T7 Real-Time Monitor")


ax1.set_ylabel("Voltage (V)")
ax1.set_title("Real-Time Analog Input Voltages")
ax1.set_ylim(Y_MIN, Y_MAX)
ax1.grid(True)
bars_voltage = ax1.bar(range(MUX_CHANNELS), [0]*MUX_CHANNELS, tick_label=[f"AIN{i}" for i in range(MUX_CHANNELS)])


ax2.set_xlabel("AIN Channel")
ax2.set_ylabel("Temperature (°C)")
ax2.set_title("Real-Time Temperature (Chebyshev Conversion)")
ax2.set_ylim(TEMP_Y_MIN, TEMP_Y_MAX)
ax2.grid(True)
bars_temp = ax2.bar(range(MUX_CHANNELS), [0]*MUX_CHANNELS, tick_label=[f"AIN{i}" for i in range(MUX_CHANNELS)])

plt.xticks(rotation=90)
plt.tight_layout()


start_time = time.time()
file_exists = os.path.isfile(CSV_FILENAME)

with open(CSV_FILENAME, mode='a', newline='') as csvfile:
    writer = csv.writer(csvfile)
    if not file_exists:
        headers = ["Timestamp"] + [f"AIN{i}_Voltage" for i in range(MUX_CHANNELS)] + [f"AIN{i}_Temp" for i in range(MUX_CHANNELS)]
        writer.writerow(headers)

    try:
        while True:
            timestamp = round(time.time() - start_time, 3)
            ain_names = [f"AIN{i}" for i in range(MUX_CHANNELS)]
            voltages = ljm.eReadNames(handle, MUX_CHANNELS, ain_names)
            temperatures = [round(cheb_eq(v), 3) for v in voltages]

            
            for bar, voltage in zip(bars_voltage, voltages):
                bar.set_height(voltage)

            
            for bar, temp in zip(bars_temp, temperatures):
                bar.set_height(temp)

            
            row = [timestamp] + [round(v, 3) for v in voltages] + temperatures
            writer.writerow(row)
            csvfile.flush()

            plt.pause(0.01)
            time.sleep(SAMPLING_INTERVAL)

    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")

    finally:
        ljm.close(handle)
        print("LabJack connection closed.")