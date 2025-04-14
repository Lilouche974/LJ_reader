import time
import csv
import numpy as np
import matplotlib.pyplot as plt
from labjack import ljm

# ====== Config ======
SAMPLING_INTERVAL = 0.2  # seconds (5 Hz)
CSV_VOLTAGE_FILE = 'time_voltage.csv'
CSV_TEMP_FILE = 'time_temp.csv'
# =====================

# --- Chebyshev Voltage-to-Temperature Conversion ---
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
    """
    Chebyshev polynomial for voltage to temperature conversion.
    """
    offset_v = 2.289562
    Zv = Zv - offset_v  # Adjust the input voltage
    k = ((Zv - Zl) - (Zu - Zv)) / (Zu - Zl)
    acos_k = np.arccos(k)
    return (
        a0 * np.cos(0 * acos_k) +
        a1 * np.cos(1 * acos_k) +
        a2 * np.cos(2 * acos_k) +
        a3 * np.cos(3 * acos_k) +
        a4 * np.cos(4 * acos_k) +
        a5 * np.cos(5 * acos_k) +
        a6 * np.cos(6 * acos_k)
    )

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
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
fig.canvas.manager.set_window_title("LabJack T7 Real-Time Voltage and Temperature Monitor")

# Top plot: Voltage
ax1.set_ylabel("Voltage (V)")
ax1.set_title("Real-Time Voltage (AIN1 - AIN0 and AIN1)", fontsize=14)
ax1.grid(True)
line_voltage, = ax1.plot([], [], label="Real Voltage (AIN1 - AIN0)", lw=2)
line_ain1, = ax1.plot([], [], label="AIN1", lw=2, linestyle="--")
ax1.legend(loc='upper left')

# Bottom plot: Temperature
ax2.set_xlabel("Time (s)")
ax2.set_ylabel("Temperature (K)")
ax2.set_title("Real-Time Temperature", fontsize=14)
ax2.grid(True)
line_temp, = ax2.plot([], [], label="Temperature (K)", lw=2, color="red")
ax2.legend(loc='upper left')

plt.tight_layout()

# --- Data Buffers ---
time_data = []
real_voltage_data = []
ain1_data = []
temp_data = []
start_time = time.time()

# Open CSV files for real-time writing
voltage_csv = open(CSV_VOLTAGE_FILE, mode='w', newline='')
temp_csv = open(CSV_TEMP_FILE, mode='w', newline='')
voltage_writer = csv.writer(voltage_csv)
temp_writer = csv.writer(temp_csv)

# Write CSV headers
voltage_writer.writerow(["Time (s)", "Real Voltage (V)", "AIN1 (V)"])
temp_writer.writerow(["Time (s)", "Temperature (K)"])

try:
    while True:
        # Read AIN0 and AIN1
        ain0, ain1 = ljm.eReadNames(handle, 2, ["AIN0", "AIN1"])
        now = time.time() - start_time

        # Compute real voltage and temperature
        real_voltage = ain1 - ain0
        try:
            temp_kelvin = cheb_eq(real_voltage)
        except Exception:
            temp_kelvin = np.nan  # Handle invalid voltage for temperature conversion

        # Append data to buffers
        time_data.append(now)
        real_voltage_data.append(real_voltage)
        ain1_data.append(ain1)
        temp_data.append(temp_kelvin)

        # Write data to CSV in real-time
        voltage_writer.writerow([now, real_voltage, ain1])
        temp_writer.writerow([now, temp_kelvin])

        # Trim old data to avoid memory overflow
        if len(time_data) > 1000:  # Keep only the last 1000 points
            time_data = time_data[-1000:]
            real_voltage_data = real_voltage_data[-1000:]
            ain1_data = ain1_data[-1000:]
            temp_data = temp_data[-1000:]

        # Update plots
        line_voltage.set_data(time_data, real_voltage_data)
        line_ain1.set_data(time_data, ain1_data)
        line_temp.set_data(time_data, temp_data)

        # Autoscale axes with tight windows around the averages
        if len(real_voltage_data) > 0:
            avg_voltage = np.mean(real_voltage_data)
            voltage_margin = max(0.1, 0.1 * (max(real_voltage_data) - min(real_voltage_data)))  # ±10% or minimum margin
            ax1.set_ylim(avg_voltage - voltage_margin, avg_voltage + voltage_margin)

        if len(temp_data) > 0:
            avg_temp = np.mean(temp_data)
            temp_margin = max(1, 0.1 * (max(temp_data) - min(temp_data)))  # ±10% or minimum margin
            ax2.set_ylim(avg_temp - temp_margin, avg_temp + temp_margin)

        ax1.set_xlim(min(time_data), max(time_data))
        ax2.set_xlim(min(time_data), max(time_data))

        plt.pause(0.01)
        time.sleep(SAMPLING_INTERVAL)

except KeyboardInterrupt:
    print("\nStopped by user.")

finally:
    # Close LabJack handle and CSV files
    ljm.close(handle)
    voltage_csv.close()
    temp_csv.close()
    plt.ioff()
    plt.show()
    print("LabJack handle closed. Data saved to CSV files.")