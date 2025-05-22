import time
import numpy as np
import matplotlib.pyplot as plt
import csv
import os
from labjack import ljm
from matplotlib.widgets import Slider, Button

# ====================== CONFIGURATION ======================
SAMPLING_INTERVAL = 0.25  # Time between samples in seconds
MUX_CHANNELS = 120        # Number of analog input channels to monitor
Y_MIN, Y_MAX = -10.0, 10.0  # Voltage range for plots
TEMP_Y_MIN, TEMP_Y_MAX = -100, 400  # Temperature range for plots
CSV_FILENAME = "labjack_data.csv"  # File to store logged data
INITIAL_TIME_WINDOW = 60  # Initial time window to display (seconds)
PLOT_UPDATE_INTERVAL = 10  # How often to update plots (in iterations)

# Chebyshev polynomial coefficients for temperature conversion
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
    """Convert voltage reading to temperature using Chebyshev polynomial approximation.
    
    Args:
        Zv: Voltage reading from thermocouple
        
    Returns:
        Calculated temperature in °C
    """
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

# ====================== LABJACK SETUP ======================
# Connect to LabJack device
handle = ljm.openS("T7", "ANY", "ANY")
info = ljm.getHandleInfo(handle)
print(f"\nConnected to LabJack T7 | Serial: {info[2]}, IP: {ljm.numberToIP(info[3])}\n")

# Configure all AIN channels for ±10V range
ain_settings = [f"AIN{i}_RANGE" for i in range(MUX_CHANNELS)]
ain_values = [10.0] * MUX_CHANNELS
ljm.eWriteNames(handle, len(ain_settings), ain_settings, ain_values)
print(f"Configured {MUX_CHANNELS} AIN channels for ±10V range.\n")

# ====================== PLOT SETUP ======================
plt.ion()  # Enable interactive mode for real-time plotting
fig = plt.figure(figsize=(16, 12))
fig.canvas.manager.set_window_title("LabJack T7 Real-Time Monitor")

# Create grid layout for our plots
gs = fig.add_gridspec(3, 2)
ax1 = fig.add_subplot(gs[0, 0])  # Voltage bar plot (top-left)
ax2 = fig.add_subplot(gs[1, 0])  # Temp bar plot (middle-left)
ax3 = fig.add_subplot(gs[0:2, 1])  # Selected channel time plot (right side)
ax4 = fig.add_subplot(gs[2, :])   # Mini time plots for all channels (bottom)

# 1. VOLTAGE BAR PLOT (Top-left)
ax1.set_ylabel("Voltage (V)")
ax1.set_title("Real-Time Analog Input Voltages")
ax1.set_ylim(Y_MIN, Y_MAX)
ax1.grid(True)
bars_voltage = ax1.bar(range(MUX_CHANNELS), [0]*MUX_CHANNELS, 
                      tick_label=[f"AIN{i}" for i in range(MUX_CHANNELS)])

# 2. TEMPERATURE BAR PLOT (Middle-left)
ax2.set_xlabel("AIN Channel")
ax2.set_ylabel("Temperature (°C)")
ax2.set_title("Real-Time Temperature (Chebyshev Conversion)")
ax2.set_ylim(TEMP_Y_MIN, TEMP_Y_MAX)
ax2.grid(True)
bars_temp = ax2.bar(range(MUX_CHANNELS), [0]*MUX_CHANNELS, 
                   tick_label=[f"AIN{i}" for i in range(MUX_CHANNELS)])

# 3. DETAILED TIME PLOT (Right side)
ax3.set_title("Individual Channel Voltage vs Time (AIN0)")
ax3.set_xlabel("Time (s)")
ax3.set_ylabel("Voltage (V)")
ax3.grid(True)
time_plot, = ax3.plot([], [], 'b-', label='Voltage')
ax3.legend()
ax3.set_xlim(0, INITIAL_TIME_WINDOW)  # Start with 60-second window
ax3.set_ylim(Y_MIN, Y_MAX)

# 4. ALL CHANNELS OVERVIEW PLOT (Bottom)
ax4.set_title("All Channels Overview (Voltage vs Time)")
ax4.set_xlabel("Time (s)")
ax4.set_ylabel("Channel")
ax4.set_yticks(range(0, MUX_CHANNELS, 10))  # Label every 10th channel
ax4.set_ylim(-1, MUX_CHANNELS)  # Set y-axis to match channel numbers
ax4.grid(True)

# Create lines for all mini plots (one per channel)
mini_lines = []
for i in range(MUX_CHANNELS):
    line, = ax4.plot([], [], lw=0.5)
    mini_lines.append(line)

# ====================== DATA STORAGE ======================
# Store complete history of all measurements
time_history = []  # List to store all timestamps
voltage_history = [[] for _ in range(MUX_CHANNELS)]  # List of lists for each channel's voltages
current_channel = 0  # Default to showing AIN0

# ====================== INTERACTIVE CONTROLS ======================
# Add slider for channel selection
ax_slider = fig.add_axes([0.15, 0.02, 0.65, 0.03])
channel_slider = Slider(
    ax=ax_slider,
    label='Channel Selector',
    valmin=0,
    valmax=MUX_CHANNELS-1,
    valinit=0,
    valstep=1
)

def update_channel(val):
    """Callback function for channel selection slider."""
    global current_channel
    current_channel = int(val)
    ax3.set_title(f"AIN{current_channel} Voltage vs Time")
    # Auto-adjust x-axis limits when changing channels
    if time_history:
        ax3.set_xlim(0, max(INITIAL_TIME_WINDOW, time_history[-1]))
    
channel_slider.on_changed(update_channel)

plt.tight_layout()
plt.subplots_adjust(bottom=0.1)  # Adjust layout to make room for slider

# ====================== DATA LOGGING ======================
start_time = time.time()
file_exists = os.path.isfile(CSV_FILENAME)

with open(CSV_FILENAME, mode='a', newline='') as csvfile:
    writer = csv.writer(csvfile)
    if not file_exists:
        headers = ["Timestamp"] + [f"AIN{i}_Voltage" for i in range(MUX_CHANNELS)] + [f"AIN{i}_Temp" for i in range(MUX_CHANNELS)]
        writer.writerow(headers)

    try:
        iteration_count = 0
        while True:
            # Get current timestamp
            timestamp = round(time.time() - start_time, 3)
            
            # Read all analog input channels
            ain_names = [f"AIN{i}" for i in range(MUX_CHANNELS)]
            voltages = ljm.eReadNames(handle, MUX_CHANNELS, ain_names)
            
            # Convert voltages to temperatures
            temperatures = [round(cheb_eq(v), 3) for v in voltages]

            # Store data in history
            time_history.append(timestamp)
            for i in range(MUX_CHANNELS):
                voltage_history[i].append(voltages[i])

            # Update bar plots (every iteration)
            for bar, voltage in zip(bars_voltage, voltages):
                bar.set_height(voltage)

            for bar, temp in zip(bars_temp, temperatures):
                bar.set_height(temp)

            # Update plots less frequently to improve performance
            if iteration_count % PLOT_UPDATE_INTERVAL == 0:
                # Update selected channel time plot
                time_plot.set_data(time_history, voltage_history[current_channel])
                
                # Auto-expand x-axis as time progresses
                if time_history:
                    ax3.set_xlim(0, max(INITIAL_TIME_WINDOW, time_history[-1]))
                
                # Update mini time plots (vertically offset for visibility)
                for i, line in enumerate(mini_lines):
                    # Offset each channel's data by its channel number
                    offset_voltage = [v + i for v in voltage_history[i]]
                    line.set_data(time_history, offset_voltage)
                
                # Auto-expand x-axis for overview plot
                if time_history:
                    ax4.set_xlim(0, max(INITIAL_TIME_WINDOW, time_history[-1]))

            # Write to CSV file
            row = [timestamp] + [round(v, 3) for v in voltages] + temperatures
            writer.writerow(row)
            csvfile.flush()

            # Pause briefly to allow plot updates and maintain sampling rate
            plt.pause(0.01)
            time.sleep(SAMPLING_INTERVAL)
            iteration_count += 1

    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")

    finally:
        # Clean up resources
        ljm.close(handle)
        print("LabJack connection closed.")
        print(f"Data saved to {CSV_FILENAME}")