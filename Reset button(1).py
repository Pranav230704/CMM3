# -*- coding: utf-8 -*-
"""
Created on Tue Nov  5 13:27:43 2024

@author: Findlay
"""

import numpy as np
import yaml
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from meteostat import Point, Hourly

# Define the location (Edinburgh: 55.9533° N, 3.1883° W)
location = Point(55.9533, -3.1883)
# Set the time period for data retrieval
start = datetime(2023, 1, 1, 0)  # Start time
end = datetime(2023, 1, 2, 0)    # End time (24-hour period)
# Fetch hourly temperature data
data = Hourly(location, start, end)
data = data.fetch()
T_amb_list = data['temp'].tolist()

# Open COP YAML file
file_path1 = r'/Users/Findlay/Downloads/heat_pump_cop_synthetic_full.yaml' #\Users\Findlay\Downloads\heat_pump_cop_synthetic_full.yaml"
with open(file_path1, 'r') as file:
    cop_yaml = yaml.safe_load(file)

cop_temp = []
cop_cop = []

# Pick out data from YAML file
for i in cop_yaml['heat_pump_cop_data']:
    cop_temp.append(i['outdoor_temp_C'])
    cop_cop.append(i['COP_noisy'])

class Heat_System:
    def __init__(self, Aw, Uw, Ar, Ur, T_amb_list, T_sp, U_cond, T_cond, U_tank, c_t):
        self.Aw = Aw
        self.Uw = Uw
        self.Ar = Ar
        self.Ur = Ur
        self.T_amb_list = T_amb_list
        self.T_sp = T_sp
        self.U_cond = U_cond
        self.T_cond = T_cond
        self.U_tank = U_tank
        self.c_t = c_t
        self.pump_on = False

    def Q_load(self):
        Q_loads = []
        for i, Tamb in enumerate(self.T_amb_list):
            Q_load = self.Aw * self.Uw * (Tamb + 273 - self.T_sp) + self.Ar * self.Ur * (Tamb + 273 - self.T_sp)
            Q_loads.append(Q_load)
        return Q_loads

    def Q_hp(self, T_tank):
        if T_tank >= 60 + 273.15:
            self.pump_on = False
        elif T_tank <= 40 + 273.15:
            self.pump_on = True
        if self.pump_on:
            return self.U_cond * (self.T_cond - T_tank)
        else:
            return 0

    def tank_temperature_ode(self, t, T_tank):
        Q_hp = self.Q_hp(T_tank)
        Load = np.interp(t, np.linspace(0, 86400, len(self.Q_load())), self.Q_load())
        T_amb = np.interp(t, np.linspace(0, 86400, len(self.T_amb_list)), self.T_amb_list)
        Q_loss = self.U_tank * (T_tank - T_amb)
        dTdt = (Q_hp - Load - Q_loss) / self.c_t
        return dTdt

    def solve_tank_temperature(self, initial_tank_temp, total_time=86400, time_points=1000):
        t_eval = np.linspace(0, total_time, time_points)
        solution = solve_ivp(self.tank_temperature_ode, [0, total_time], [initial_tank_temp], t_eval=t_eval, method="RK45")
        T_tank_values = solution.y[0] - 273.15  # Convert to °C
        time_values = solution.t
        return time_values, T_tank_values

def run_simulation(Aw, Uw, Ar, Ur, T_sp, U_cond, T_cond, U_tank, c_t, display_type):
    heat_system = Heat_System(Aw, Uw, Ar, Ur, T_amb_list, T_sp, U_cond, T_cond, U_tank, c_t)
    initial_tank_temp = 318.15  # Initial tank temperature in K
    time_values, T_tank_values = heat_system.solve_tank_temperature(initial_tank_temp)

    if display_type == 'Temperature':
        plt.figure()
        plt.plot(time_values / 3600, T_tank_values)
        plt.xlabel("Time (hours)")
        plt.ylabel("Tank Temperature (°C)")
        plt.title("Tank Temperature Over Time")
        plt.grid(True)
        plt.show()

# Initialize the main application window
root = tk.Tk()
root.title("Heat Pump Simulation")

# Function to set parameters from predefined buttons
def set_parameters(params):
    Aw_entry.delete(0, tk.END)
    Aw_entry.insert(0, params['Aw'])
    Uw_entry.delete(0, tk.END)
    Uw_entry.insert(0, params['Uw'])
    Ar_entry.delete(0, tk.END)
    Ar_entry.insert(0, params['Ar'])
    Ur_entry.delete(0, tk.END)
    Ur_entry.insert(0, params['Ur'])
    T_sp_entry.delete(0, tk.END)
    T_sp_entry.insert(0, params['T_sp'])

# Frame for Parameters
frame_params = tk.Frame(root)
frame_params.pack(padx=10, pady=10)

# Entry fields for parameters
tk.Label(frame_params, text="Wall Area in m² (Aw):").grid(row=0, column=0)
Aw_entry = tk.Entry(frame_params)
Aw_entry.grid(row=0, column=1)

tk.Label(frame_params, text="Wall U-value in W/m²K (Uw):").grid(row=1, column=0)
Uw_entry = tk.Entry(frame_params)
Uw_entry.grid(row=1, column=1)

tk.Label(frame_params, text="Roof Area in m² (Ar):").grid(row=2, column=0)
Ar_entry = tk.Entry(frame_params)
Ar_entry.grid(row=2, column=1)

tk.Label(frame_params, text="Roof U-value in W/m²K (Ur):").grid(row=3, column=0)
Ur_entry = tk.Entry(frame_params)
Ur_entry.grid(row=3, column=1)

tk.Label(frame_params, text="Set Point Temperature in K (T_sp):").grid(row=4, column=0)
T_sp_entry = tk.Entry(frame_params)
T_sp_entry.grid(row=4, column=1)

# Predefined parameter settings for buttons A, B, and C
parameter_settings = {
    'A': {'Aw': 90, 'Uw': 0.3, 'Ar': 80, 'Ur': 0.15, 'T_sp': 303.15},
    'B': {'Aw': 132, 'Uw': 0.51, 'Ar': 120, 'Ur': 0.18, 'T_sp': 293.15},
    'C': {'Aw': 180, 'Uw': 0.75, 'Ar': 150, 'Ur': 0.25, 'T_sp': 280.15}
}

# Create buttons for parameter sets A, B, C
tk.Button(frame_params, text="Parameters A", command=lambda: set_parameters(parameter_settings['A'])).grid(row=6, column=0, pady=5)
tk.Button(frame_params, text="Parameters B", command=lambda: set_parameters(parameter_settings['B'])).grid(row=6, column=1, pady=5)
tk.Button(frame_params, text="Parameters C", command=lambda: set_parameters(parameter_settings['C'])).grid(row=6, column=2, pady=5)

# Reset function to set all parameters to 0
def reset_fields():
    Aw_entry.delete(0, tk.END)
    Aw_entry.insert(0, 0)

    Uw_entry.delete(0, tk.END)
    Uw_entry.insert(0, 0)

    Ar_entry.delete(0, tk.END)
    Ar_entry.insert(0, 0)

    Ur_entry.delete(0, tk.END)
    Ur_entry.insert(0, 0)

    T_sp_entry.delete(0, tk.END)
    T_sp_entry.insert(0, 0)

# Add reset button to the frame
reset_button = tk.Button(frame_params, text="Reset Parameters to 0", command=reset_fields)
reset_button.grid(row=7, columnspan=2, pady=10)

# Frame for Performance Metrics
frame_metrics = tk.Frame(root)
frame_metrics.pack(padx=10, pady=10)

# Section for performance metrics
tk.Label(frame_metrics, text="Select Performance Metric:").pack()

# Dropdown menu for performance metrics
performance_metric_var = tk.StringVar(value="Select Metric")
performance_metrics = ["Energy Consumption", "Coefficient of Performance", "Maximum Thermal Output", "Total System Efficiency"]
metric_dropdown = ttk.Combobox(frame_metrics, textvariable=performance_metric_var, values=performance_metrics)
metric_dropdown.pack(pady=5)

# Function to show performance metric graph
def show_performance_metric():
    selected_metric = performance_metric_var.get()
    if selected_metric == "Select Metric":
        return  # Do nothing if no metric is selected

    plt.figure()
    time = np.linspace(0, 24, 100)  # Dummy time data

    if selected_metric == "Energy Consumption":
        energy = np.sin(time) + 1  # Dummy data, replace with actual energy consumption data
        plt.plot(time, energy)
        plt.title("Energy Consumption Over Time")
        plt.xlabel("Time (h)")
        plt.ylabel("Energy (kWh)")
    elif selected_metric == "Coefficient of Performance":
        cop = np.cos(time) + 3  # Dummy data, replace with actual COP data
        plt.plot(time, cop)
        plt.title("Coefficient of Performance Over Time")
        plt.xlabel("Time (h)")
        plt.ylabel("COP")
    elif selected_metric == "Maximum Thermal Output":
        thermal_output = np.random.uniform(0, 100, size=100)  # Dummy data
        plt.plot(time, thermal_output)
        plt.title("Maximum Thermal Output Over Time")
        plt.xlabel("Time (h)")
        plt.ylabel("Thermal Output (kW)")
    elif selected_metric == "Total System Efficiency":
        efficiency = np.random.uniform(0, 100, size=100)  # Dummy data
        plt.plot(time, efficiency)
        plt.title("Total System Efficiency Over Time")
        plt.xlabel("Time (h)")
        plt.ylabel("Efficiency (%)")

    plt.grid(True)
    plt.show()

# Button to display the selected performance metric
tk.Button(frame_metrics, text="Show Metric", command=show_performance_metric).pack(pady=10)

# Frame for Simulation Control
frame_simulation = tk.Frame(root)
frame_simulation.pack(padx=10, pady=10)

# Define additional parameters for simulation
U_cond = 300
T_cond = 343.15
U_tank = 5
c_t = 837200

# Placeholder function for running simulation
def run_simulation(Aw, Uw, Ar, Ur, T_sp, U_cond, T_cond, U_tank, c_t, metric):
    print("Running simulation with the following parameters:")
    print(f"Aw: {Aw}, Uw: {Uw}, Ar: {Ar}, Ur: {Ur}, T_sp: {T_sp}")
    # Implement your simulation logic here

# Button to start the simulation
tk.Button(frame_simulation, text="Run Simulation", command=lambda: run_simulation(
    float(Aw_entry.get()),
    float(Uw_entry.get()),
    float(Ar_entry.get()),
    float(Ur_entry.get()),
    float(T_sp_entry.get()),
    U_cond,
    T_cond,
    U_tank,
    c_t,
    'Temperature')).pack(pady=10)

# Start the main application loop
root.mainloop()
