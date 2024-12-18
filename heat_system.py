# Heat System Simulation Code

# Capabilities:
# - Simulates the behavior of a heat pump system.
# - Calculates heat load and tank temperature dynamics.
# - Calculates Perfomance Metrics.
# - Solves tank temperature using a differential equation model.

# Limitations:
# - Assumes a fixed heat pump condenser temperature.
# - Does not fully account for real-world variables such as variable flow rates, weather conditions.

import numpy as np
import yaml
from scipy.integrate import solve_ivp
from scipy.optimize import curve_fit

# Load COP data from YAML file
file_path1 = r'/example/filepath/group6/heat_pump_cop_synthetic_full.yaml' # this is an example filepath, please change it accordingly
with open(file_path1, 'r') as file:
    cop_yaml = yaml.safe_load(file)

cop_temp = []
cop_cop = []

# Pick out data from yaml file
for i in cop_yaml['heat_pump_cop_data']:
    cop_temp.append(i['outdoor_temp_C'])  # extract outdoor temperature data
    cop_cop.append(i['COP_noisy'])  # extract COP (with noise) data


class Heat_system:
    def __init__(self, Aw, Uw, Ar, Ur, T_amb_list, T_sp, U_cond, T_cond, U_tank, A_tank, c_t, A_cond):
        # initializing system properties for the heat pump and thermal storage
        self.Aw = Aw  # wall area (m^2)
        self.Uw = Uw  # wall U-value (W/m^2K)
        self.Ar = Ar  # roof area (m^2)
        self.Ur = Ur  # roof U-value (W/m^2K)
        self.T_amb_list = T_amb_list  # list of ambient temperatures for 24 hours
        self.T_sp = T_sp  # indoor set point temperature (K)
        self.U_cond = U_cond  # heat transfer coefficient for condenser
        self.T_cond = T_cond  # fixed condenser temperature (K)
        self.U_tank = U_tank  # heat transfer coefficient for the tank
        self.A_tank = A_tank  # surface area of the tank (m^2)
        self.c_t = c_t  # thermal capacity of the tank (J/K)
        self.A_cond = A_cond  # surface area of condenser (m^2)
        self.pump_on = False  # initial state of the heat pump
        self.real_cop = []  # to store real COP values (later used for analysis)
        self.cop_values = []  # to store COP values over time

    def Q_load(self):
        # calculate heat load based on house characteristics and ambient temperature
        Q_loads = []
        for Tamb in self.T_amb_list:
            # heat load calculated using house envelope parameters (negative because heat is leaving)
            Q_load = (self.Aw * self.Uw * (Tamb + 273 - self.T_sp) + self.Ar * self.Ur * (Tamb + 273 - self.T_sp)) * -1
            Q_loads.append(Q_load)
        return Q_loads

    def cop(self, T_amb, a, b):
        # calculate the coefficient of performance (COP) based on ambient temperature
        delta_T = 60 - T_amb  # temperature difference between condenser and outdoor
        return a + b / delta_T  # empirical COP relationship using parameters a and b

    # fitting empirical COP model to given data (using linear fit)
    popt, _ = curve_fit(lambda T, a, b: a + b / (60 - T), cop_temp, cop_cop)  # determine values for a and b
    a, b = popt

    def Q_hp(self, T_tank, T_amb):
        # calculate the heat supplied by the heat pump based on tank temperature and pump status
        if T_tank >= 60 + 273.15:
            self.pump_on = False  # turn off pump when tank temperature exceeds 60°C
        elif T_tank <= 40 + 273.15:
            self.pump_on = True  # turn on pump when tank temperature drops below 40°C

        if self.pump_on:
            return self.A_cond * (self.U_cond * (self.T_cond - T_tank))  # heat supplied by condenser
        else:
            return 0  # no heat supplied if pump is off

    def tank_temperature_ode(self, t, T_tank):
        # ordinary differential equation for tank temperature dynamics
        T_amb = np.interp(t, np.linspace(0, 86400, len(self.T_amb_list)), self.T_amb_list)  # interpolate ambient temperature over time in seconds to fit the index
        Load = np.interp(t, np.linspace(0, 86400, len(self.Q_load())), self.Q_load())  # interpolate load over time in seconds to fit the index
        Q_hp = self.Q_hp(T_tank, T_amb)  # calculate heat pump output
        Q_loss = self.U_tank * self.A_tank * (T_tank - T_amb)  # heat loss from tank to environment

        dTdt = (Q_hp - Load - Q_loss) / self.c_t  # rate of change of tank temperature
        return dTdt

    def solve_tank_temperature(self, initial_tank_temp, total_time=86400, time_points=1000):
        # solve the ODE for tank temperature over a 24-hour period
        t_eval = np.linspace(0, total_time, time_points)  # define evaluation points for time
        T_amb_interpolated = np.interp(t_eval, np.linspace(0, 86400, len(self.T_amb_list)), self.T_amb_list)  # interpolate ambient temperatures in seconds to fit the index

        solution = solve_ivp(self.tank_temperature_ode, [0, total_time], [initial_tank_temp], t_eval=t_eval, method="RK45", max_step=100)  # solve ODE using Runge-Kutta method
        self.cop_values = [self.cop(T_amb, self.a, self.b) for T_amb in T_amb_interpolated]  # calculate COP values over time

        Q_hp_values = [self.Q_hp(T_tank, T_amb) for T_tank, T_amb in zip(solution.y[0], T_amb_interpolated)]  # calculate heat pump output values
        Q_hp_total = np.trapz(Q_hp_values, t_eval)  # calculate total heat provided by the heat pump over the time period

        avg_cop = np.mean(self.cop_values) if self.cop_values else 0  # calculate average COP over the time period

        T_tank_values = solution.y[0] - 273.15  # convert temperatures from Kelvin to Celsius
        time_values = solution.t  # extract time values from solution

        return time_values, T_tank_values, Q_hp_total, avg_cop, self.cop_values


# Function to run the heat system simulation
def run_heat_system_simulation(Aw, Uw, Ar, Ur, T_amb_list, T_sp, U_cond, T_cond, U_tank, A_tank, c_t, A_cond, initial_tank_temp=318.15):
    # initialize an instance of Heat_system with the specified parameters
    heat_system = Heat_system(Aw, Uw, Ar, Ur, T_amb_list, T_sp, U_cond, T_cond, U_tank, A_tank, c_t, A_cond)
    return heat_system.solve_tank_temperature(initial_tank_temp)  # solve the tank temperature and return results
