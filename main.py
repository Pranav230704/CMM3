# main.py
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from meteostat import Point, Hourly
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from Heat_system import run_heat_system_simulation

# Define coordinates for additional cities
cities = {
    'Edinburgh': Point(55.9533, -3.1883),
    'Oslo': Point(59.9139, 10.7522),
    'Harbin': Point(45.8038, 126.5347),
    'Toronto': Point(43.65107, -79.347015),
    'Nairobi': Point(-1.286389, 36.817223),
    'Rio de Janeiro': Point(-22.9068, -43.1729),
    'Cape Town': Point(-33.9249, 18.4241)
}

# Define T_amb_list as a global variable
T_amb_list = []

# Function to get temperature for selected city
def get_temperature_for_city(city_name):
    global T_amb_list
    location = cities.get(city_name)
    if location:
        start = datetime(2023, 1, 1, 0)
        end = datetime(2023, 1, 2, 0)
        data = Hourly(location, start, end).fetch()
        T_amb_list = data['temp'].tolist()
        return T_amb_list
    else:
        return []

# Function to update temperature based on selected city
def update_temperature():
    selected_city = city_var.get()
    global T_amb_list  # Declare as global to use the updated list
    T_amb_list = get_temperature_for_city(selected_city)
    if T_amb_list:
        print(f"Temperature data for {selected_city} fetched successfully!")
        # Update the outside temperature display
        outside_temp_entry.delete(0, tk.END)
        outside_temp_entry.insert(0, f"{T_amb_list[0]:.2f}")
    else:
        print(f"Failed to fetch temperature data for {selected_city}.")

# Function to run the simulation
def run_simulation(Aw, Uw, Ar, Ur, T_sp, U_cond, T_cond, U_tank, A_tank, c_t, A_cond):
    if not T_amb_list:
        print("Temperature data not available!")
        return

    time_values, T_tank_values, Q_hp_total, avg_cop, cop_values = run_heat_system_simulation(
        Aw, Uw, Ar, Ur, T_amb_list, T_sp, U_cond, T_cond, U_tank, A_tank, c_t, A_cond
    )

    # Plotting and embedding plots in tkinter
    fig, ax = plt.subplots(figsize=(5.5, 3.75))
    ax.plot(time_values / 3600, T_tank_values, label="Tank Temperature", linewidth=1.5)
    ax.axhline(y=60, color="red", linestyle="--", label="Heat Pump Off Threshold (60°C)", linewidth=1)
    ax.axhline(y=40, color="blue", linestyle="--", label="Heat Pump On Threshold (40°C)", linewidth=1)
    ax.set_xlabel("Time (hours)", fontsize=10)
    ax.set_ylabel("Tank Temperature (°C)", fontsize=10)
    ax.set_xlim(0, 24)
    ax.set_ylim(35, 70)
    ax.set_xticks(range(0, 25, 4))
    ax.tick_params(axis='both', labelsize=9)
    ax.legend(loc="upper right", fontsize=9)
    ax.grid(True)
    plt.tight_layout()

    canvas = FigureCanvasTkAgg(fig, master=frame_temperature_plot)
    canvas.draw()
    canvas.get_tk_widget().grid(row=1, column=0, pady=10)

    # COP Plot
    fig2, ax2 = plt.subplots(figsize=(5.5, 3))
    ax2.plot(time_values / 3600, cop_values, label='COP', color='purple')
    ax2.set_xlabel('Time (hours)', fontsize=9)
    ax2.set_ylabel('COP', fontsize=9)
    ax2.set_xlim(0, 24)
    ax2.set_xticks(range(0, 25, 4))
    ax2.tick_params(axis='both', labelsize=9)
    ax2.set_title('Coefficient of Performance (COP) vs Time', fontsize=10)
    ax2.grid(True)
    plt.tight_layout()

    canvas2 = FigureCanvasTkAgg(fig2, master=frame_performance_metrics)
    canvas2.draw()
    canvas2.get_tk_widget().grid(row=1, column=0, pady=10)

    # Display total energy consumption
    energy_label.config(text=f"Total Energy Consumption: {Q_hp_total / 3.6e6:.2f} kWh")
    avg_cop_label.config(text=f"Average COP: {avg_cop:.2f}")

# Tkinter UI creation code
root = tk.Tk()
root.title("Heat Pump Simulation")
root.geometry("1400x800")
root.state('zoomed')
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)

def create_user_manual():
    user_manual = """
    Heat Pump Simulation User Manual

    This tool allows you to model and analyze the behavior of a heat pump system based on various parameters. Below is a step-by-step guide to help you get started.

1) Select one of the preset buildings (via the dropdown menu) to set the appropriate system parameters:
    
    House A: A well-insulated, smaller home.
    House B: A moderately insulated, medium-sized home.
    House C: A poorly-insulated, larger house.
    House D: The default building configuration.
    
    The inputs will be automatically filled based on the selected building.
    
2) You can edit the parameters to suit your needs. If you change the city for outside temperature, click 'Update Temperature' to refresh the temperature values.

3) Click the 'Run Simulation' button to simulate the heat pump performance and see the results.
    
4) If you wish to start again, click reset and everything will be set to 0 for you to input values again
    """
    manual_frame = tk.Frame(root, bd=2, relief=tk.GROOVE)  # Added border for separation
    manual_frame.grid(row=0, column=2, sticky='nsew', padx=20, pady=20)

    manual_label = tk.Label(manual_frame, text="User Manual", font=("Arial", 16, "bold"))
    manual_label.grid(row=0, column=0, sticky='n')

    manual_text = tk.Text(manual_frame, height=35, width=50, wrap=tk.WORD)
    manual_text.insert(tk.END, user_manual)
    manual_text.config(state=tk.DISABLED)  # Make the text widget read-only
    manual_text.grid(row=1, column=0, sticky='nsew')

# Create and display the user manual
create_user_manual()

# Reset function to reset all input fields and remove plots
def reset_fields():
    # Reset all input fields to zero
    Aw_entry.delete(0, tk.END)
    Aw_entry.insert(0, "0")
    Uw_entry.delete(0, tk.END)
    Uw_entry.insert(0, "0")
    Ar_entry.delete(0, tk.END)
    Ar_entry.insert(0, "0")
    Ur_entry.delete(0, tk.END)
    Ur_entry.insert(0, "0")
    T_sp_entry.delete(0, tk.END)
    T_sp_entry.insert(0, "0")
    mass_of_water_entry.delete(0, tk.END)
    mass_of_water_entry.insert(0, "0")
    initial_tank_temp_entry.delete(0, tk.END)
    initial_tank_temp_entry.insert(0, "0")
    on_threshold_entry.delete(0, tk.END)
    on_threshold_entry.insert(0, "0")
    off_threshold_entry.delete(0, tk.END)
    off_threshold_entry.insert(0, "0")
    A_tank_entry.delete(0, tk.END)
    A_tank_entry.insert(0, "0")
    outside_temp_entry.delete(0, tk.END)
    outside_temp_entry.insert(0, "0")
    
    # Clear city selection and house type selection
    city_var.set("Please Select")
    house_var.set("Please Select")
    
    # Clear the plots
    for widget in frame_temperature_plot.winfo_children():
        if isinstance(widget, FigureCanvasTkAgg):
            widget.get_tk_widget().destroy()
    for widget in frame_performance_metrics.winfo_children():
        if isinstance(widget, FigureCanvasTkAgg):
            widget.get_tk_widget().destroy()
    
    # Reset performance metrics labels
    energy_label.config(text="Total Energy Consumption: ")
    avg_cop_label.config(text="Average COP: ")

# Function to update the temperature based on selected city
def update_temperature_display(city_name):
    global T_amb_list  # Global variable to hold the temperature data
    # Fetch temperature data for the selected city
    T_amb_list = get_temperature_for_city(city_name)
    if T_amb_list:
        print(f"Temperature data for {city_name} fetched successfully!")
        # Set the first temperature value as the current outside temperature for display
        current_temp = T_amb_list[0]  # Assuming we're showing the first value for now
        return current_temp
    else:
        print(f"Failed to fetch temperature data for {city_name}.")
        return 0

# Modify the set_parameters function to also set the 'Outside Temp' value
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
    mass_of_water_entry.delete(0, tk.END)
    mass_of_water_entry.insert(0, params['Mass of Water in Hot Water Tank in kg'])
    
    initial_tank_temp_entry.delete(0, tk.END)
    initial_tank_temp_entry.insert(0, params['Initial Tank Temperature in K'])
    
    on_threshold_entry.delete(0, tk.END)
    on_threshold_entry.insert(0, params['Heat Pump On Threshold in K'])
    
    off_threshold_entry.delete(0, tk.END)
    off_threshold_entry.insert(0, params['Heat Pump Off Threshold in K'])
    
    A_tank_entry.delete(0, tk.END)
    A_tank_entry.insert(0, params['Tank Surface Area in m² (A_tank)'])
    
    # Set the City value (for use in fetching outside temperature)
    city_var.set(params['City'])
    
    # Fetch and display outside temperature for the city
    outside_temp = update_temperature_display(params['City'])
    # Update the outside temperature entry field
    outside_temp_entry.delete(0, tk.END)
    outside_temp_entry.insert(0, outside_temp)

# Frame for Parameters
frame_params = tk.Frame(root, bd=2, relief=tk.GROOVE)
frame_params.grid(row=0, column=0, sticky='nsew', padx=20, pady=20)

frame_params_title = tk.Label(frame_params, text="Inputs", font=("Arial", 16, "bold"))
frame_params_title.grid(row=0, column=0, columnspan=2, pady=10)

# Parameter Entry Labels and Fields
tk.Label(frame_params, text="Wall Area in m² (Aw):").grid(row=1, column=0, sticky='e')
Aw_entry = ttk.Entry(frame_params)
Aw_entry.insert(0, "0")  # Starting value
Aw_entry.grid(row=1, column=1, pady=5, padx=5)

tk.Label(frame_params, text="Wall U-value in W/m²K (Uw):").grid(row=2, column=0, sticky='e')
Uw_entry = ttk.Entry(frame_params)
Uw_entry.insert(0, "0")  # Starting value
Uw_entry.grid(row=2, column=1, pady=5, padx=5)

tk.Label(frame_params, text="Roof Area in m² (Ar):").grid(row=3, column=0, sticky='e')
Ar_entry = ttk.Entry(frame_params)
Ar_entry.insert(0, "0")  # Starting value
Ar_entry.grid(row=3, column=1, pady=5, padx=5)

tk.Label(frame_params, text="Roof U-value in W/m²K (Ur):").grid(row=4, column=0, sticky='e')
Ur_entry = ttk.Entry(frame_params)
Ur_entry.insert(0, "0")  # Starting value
Ur_entry.grid(row=4, column=1, pady=5, padx=5)

tk.Label(frame_params, text="Set Point Temperature in K (T_sp):").grid(row=5, column=0, sticky='e')
T_sp_entry = ttk.Entry(frame_params)
T_sp_entry.insert(0, "0")  # Starting value
T_sp_entry.grid(row=5, column=1, pady=5, padx=5)

tk.Label(frame_params, text="Tank Surface Area in m² (A_tank):").grid(row=6, column=0, sticky='e')
A_tank_entry = ttk.Entry(frame_params)
A_tank_entry.insert(0, "0")  # Starting value
A_tank_entry.grid(row=6, column=1, pady=5, padx=5)

# Create a new entry for displaying outside temperature
outside_temp_label = tk.Label(frame_params, text="Outside Temperature in °C (T_amb):")
outside_temp_label.grid(row=7, column=0, sticky='e')
outside_temp_entry = tk.Entry(frame_params)
outside_temp_entry.insert(0, "0")  # Default value
outside_temp_entry.grid(row=7, column=1)

tk.Label(frame_params, text="Mass of Water in Hot Water Tank in kg:").grid(row=8, column=0, sticky='e')
mass_of_water_entry = ttk.Entry(frame_params)
mass_of_water_entry.insert(0, "0")  # Starting value
mass_of_water_entry.grid(row=8, column=1, pady=5, padx=5)

tk.Label(frame_params, text="Initial Tank Temperature in K:").grid(row=9, column=0, sticky='e')
initial_tank_temp_entry = ttk.Entry(frame_params)
initial_tank_temp_entry.insert(0, "0")  # Starting value
initial_tank_temp_entry.grid(row=9, column=1, pady=5, padx=5)

tk.Label(frame_params, text="Heat Pump On Threshold in K:").grid(row=10, column=0, sticky='e')
on_threshold_entry = ttk.Entry(frame_params)
on_threshold_entry.insert(0, "0")  # Starting value
on_threshold_entry.grid(row=10, column=1, pady=5, padx=5)

tk.Label(frame_params, text="Heat Pump Off Threshold in K:").grid(row=11, column=0, sticky='e')
off_threshold_entry = ttk.Entry(frame_params)
off_threshold_entry.insert(0, "0")  # Starting value
off_threshold_entry.grid(row=11, column=1, pady=5, padx=5)

# Add the city selection dropdown
tk.Label(frame_params, text="Select City for Outside Temperature:").grid(row=12, column=0, sticky='e')
city_var = tk.StringVar(value="Please Select")  
city_dropdown = ttk.Combobox(frame_params, textvariable=city_var, values=list(cities.keys()))
city_dropdown.grid(row=12, column=1, pady=5, padx=5)

# Update temperature button
tk.Button(frame_params, text="Update Temperature", command=update_temperature).grid(row=13, column=0, columnspan=2, pady=10)

# Automatically update parameters when city selection changes
def on_house_selection_change(event):
    set_parameters(house_types[house_var.get()])

# Dropdown menu for Building Types
tk.Label(frame_params, text="House Type:").grid(row=14, column=0, sticky='e')
house_types = {
    'A': {'Aw': 85, 'Uw': 0.4, 'Ar': 80, 'Ur': 0.15, 'T_sp': 288.15,
          'Mass of Water in Hot Water Tank in kg': 160, 
          'Initial Tank Temperature in K': 318.15,
          'Heat Pump On Threshold in K': 313.15, 
          'Heat Pump Off Threshold in K': 333.15,
          'Tank Surface Area in m² (A_tank)': 0.8, 'City': 'Harbin', 'Outside Temp': 0},
    'B': {'Aw': 135, 'Uw': 0.6, 'Ar': 120, 'Ur': 0.25, 'T_sp': 298.15,
          'Mass of Water in Hot Water Tank in kg': 200,
          'Initial Tank Temperature in K': 318.15,
          'Heat Pump On Threshold in K': 313.15, 
          'Heat Pump Off Threshold in K': 333.15,
          'Tank Surface Area in m² (A_tank)': 1, 'City': 'Nairobi', 'Outside Temp': 0},
    'C': {'Aw': 180, 'Uw': 0.8, 'Ar': 160, 'Ur': 0.3, 'T_sp': 303.15,
          'Mass of Water in Hot Water Tank in kg': 240, 
          'Initial Tank Temperature in K': 318.15,
          'Heat Pump On Threshold in K': 313.15, 
          'Heat Pump Off Threshold in K': 333.15,
          'Tank Surface Area in m² (A_tank)': 1.2, 'City': 'Rio de Janeiro', 'Outside Temp': 0},
    'D': {'Aw': 132, 'Uw': 0.51, 'Ar': 120, 'Ur': 0.18, 'T_sp': 293.15,
          'Mass of Water in Hot Water Tank in kg': 200, 
          'Initial Tank Temperature in K': 318.15,
          'Heat Pump On Threshold in K': 313.15, 
          'Heat Pump Off Threshold in K': 333.15,
          'Tank Surface Area in m² (A_tank)': 1, 'City': 'Edinburgh', 'Outside Temp': 0},
}

house_var = tk.StringVar(value='Please Select')
house_dropdown = ttk.Combobox(frame_params, textvariable=house_var, values=list(house_types.keys()))
house_dropdown.grid(row=14, column=1, pady=5, padx=5)
house_dropdown.bind("<<ComboboxSelected>>", on_house_selection_change)

# Frame for running simulation
frame_simulation = tk.Frame(root, bd=2, relief=tk.GROOVE)  # Added border for separation
frame_simulation.grid(row=0, column=1, sticky='nsew', padx=20, pady=20)

frame_simulation_title = tk.Label(frame_simulation, text="Results", font=("Arial", 16, "bold"))
frame_simulation_title.grid(row=0, column=0, pady=10, sticky='n')

# Frame for Temperature Plot
frame_temperature_plot = tk.Frame(frame_simulation, bd=2, relief=tk.GROOVE, width=400, height=320)  # Adjusted size for better fit
frame_temperature_plot.grid_propagate(False)  # Prevent resizing
frame_temperature_plot.grid(row=1, column=0, padx=10, pady=10, sticky='nsew')
tk.Label(frame_temperature_plot, text="Tank Temperature vs Time", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky='n')

# Frame for Performance Metrics (including COP Plot and Energy Consumption)
frame_performance_metrics = tk.Frame(frame_simulation, bd=2, relief=tk.GROOVE, width=400, height=410)  # Adjusted size for better fit
frame_performance_metrics.grid_propagate(False)  # Prevent resizing
frame_performance_metrics.grid(row=2, column=0, padx=10, pady=10, sticky='nsew')
tk.Label(frame_performance_metrics, text="Performance Metrics", font=("Arial", 14, "bold")).grid(row=0, column=0, sticky='n')

# Display total energy consumption
energy_label = tk.Label(frame_performance_metrics, text="Total Energy Consumption: ", font=("Arial", 12, 'bold'))
energy_label.grid(row=2, column=0, pady=10)
avg_cop_label = tk.Label(frame_performance_metrics, text="Average COP: ", font=("Arial", 12, 'bold'))
avg_cop_label.grid(row=3, column=0, pady=10)

# Frame for running simulation
run_sim_button = ttk.Button(frame_params, text="Run Simulation", command=lambda: run_simulation( 
    float(Aw_entry.get()), float(Uw_entry.get()), float(Ar_entry.get()), float(Ur_entry.get()), 
    float(T_sp_entry.get()), 300, 343.15, 5, float(A_tank_entry.get()), 
    float(mass_of_water_entry.get()) * 4186, 1.11))  # Added A_cond as 1.11
run_sim_button.grid(row=15, column=0, columnspan=2, pady=10)

# Reset button to reset all fields and remove plots
reset_button = ttk.Button(frame_params, text="Reset", command=reset_fields)
reset_button.grid(row=16, column=0, columnspan=2, pady=10)

root.mainloop()
