# -*- coding: utf-8 -*-
"""
Created on Wed Oct  9 18:17:22 2024

@author: acer
"""

from datetime import datetime
from meteostat import Point, Hourly
# Define the location (Edinburgh: 55.9533° N, 3.1883° W)
location = Point(55.9533, -3.1883)
# Set the time period for data retrieval
start = datetime(2023, 1, 1, 0) # Start time
end = datetime(2023, 1, 2, 0) # End time (24-hour period)
# Fetch hourly temperature data
data = Hourly(location, start, end)
data = data.fetch()

for index, row in data.iterrows():
    print(f"Time: {index}, Temperature: {row['temp']}°C")

import numpy as np
import yaml
import sympy as sym

sym.init_printing()

with open(r'C:\Users\acer\Downloads\heat_pump_cop_synthetic_full (1).yaml') as file:
    data = yaml.safe_load(file)
    
outdoor_temps = []
cop_values = []

for y in data['heat_pump_cop_data']:
    outdoor_temps.append(y['outdoor_temp_C'])
    cop_values.append(y['COP_noisy'])

outdoor_temps = np.array(outdoor_temps)
cop_values = np.array(cop_values)

print("Outdoor temperatures:", outdoor_temps)  
print("COP values:", cop_values)

fixed_temp = 60 
delta_T = fixed_temp - outdoor_temps
a, b = sym.symbols('a b')

g = [
    sym.Eq(a + b / delta_T[i], cop_values[i]) for i in range(2)  # Using the first two data points
]
    
sym.solve(g, (a, b))

with open(r'C:\Users\acer\Downloads\inputs (1).yaml') as file:
    data = yaml.safe_load(file)
    

A_w = data['building_properties']['wall_area']['value']
U_w = data['building_properties']['wall_U_value']['value']
A_r = data['building_properties']['roof_area']['value']
U_r = data['building_properties']['roof_U_value']['value']
T_amb = outdoor_temps + 273
T_sp = data['building_properties']['indoor_setpoint_temperature_K']['value']
    

Q_load = ((A_w * U_w * (T_amb - T_sp)) + (A_r * U_r * (T_amb - T_sp)))

(Q_load)