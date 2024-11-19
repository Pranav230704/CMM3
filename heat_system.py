### File 1: `heat_system.py`
#This file will include the heat system simulation class and functions.


# heat_system.py
import numpy as np
import yaml
from scipy.integrate import solve_ivp
from scipy.optimize import curve_fit

# Load COP data from YAML file
file_path1 = r'/Users/pranav/Downloads/heat_pump_cop_synthetic_full.yaml'
with open(file_path1, 'r') as file:
    cop_yaml = yaml.safe_load(file)

cop_temp = []
cop_cop = []

# Pick out data from yaml file
for i in cop_yaml['heat_pump_cop_data']:
    cop_temp.append(i['outdoor_temp_C'])
    cop_cop.append(i['COP_noisy'])

class Heat_system:
    def __init__(self, Aw, Uw, Ar, Ur, T_amb_list, T_sp, U_cond, T_cond, U_tank, A_tank, c_t, A_cond):
        self.Aw = Aw
        self.Uw = Uw
        self.Ar = Ar
        self.Ur = Ur
        self.T_amb_list = T_amb_list
        self.T_sp = T_sp
        self.U_cond = U_cond
        self.T_cond = T_cond
        self.U_tank = U_tank
        self.A_tank = A_tank
        self.c_t = c_t
        self.A_cond = A_cond
        self.pump_on = False
        self.real_cop = []  
        self.cop_values = []

    def Q_load(self):
        Q_loads = []
        for Tamb in self.T_amb_list:
            Q_load = (self.Aw * self.Uw * (Tamb + 273 - self.T_sp) + self.Ar * self.Ur * (Tamb + 273 - self.T_sp)) * -1
            Q_loads.append(Q_load)
        return Q_loads

    def cop(self, T_amb, a, b):
        delta_T = 60 - T_amb
        return a + b / delta_T

    popt, _ = curve_fit(lambda T, a, b: a + b / (60 - T), cop_temp, cop_cop)
    a, b = popt

    def Q_hp(self, T_tank, T_amb):
        if T_tank >= 60 + 273.15:
            self.pump_on = False
        elif T_tank <= 40 + 273.15:
            self.pump_on = True

        if self.pump_on:
            return self.A_cond * (self.U_cond * (self.T_cond - T_tank))
        else:
            return 0

    def tank_temperature_ode(self, t, T_tank):
        T_amb = np.interp(t, np.linspace(0, 86400, len(self.T_amb_list)), self.T_amb_list)
        Load = np.interp(t, np.linspace(0, 86400, len(self.Q_load())), self.Q_load())
        Q_hp = self.Q_hp(T_tank, T_amb)
        Q_loss = self.U_tank * self.A_tank * (T_tank - T_amb)

        dTdt = (Q_hp - Load - Q_loss) / self.c_t
        return dTdt

    def solve_tank_temperature(self, initial_tank_temp, total_time=86400, time_points=1000):
        t_eval = np.linspace(0, total_time, time_points)
        T_amb_interpolated = np.interp(t_eval, np.linspace(0, 86400, len(self.T_amb_list)), self.T_amb_list)

        solution = solve_ivp(self.tank_temperature_ode, [0, total_time], [initial_tank_temp], t_eval=t_eval, method="RK45", max_step=100)
        self.cop_values = [self.cop(T_amb, self.a, self.b) for T_amb in T_amb_interpolated]

        Q_hp_values = [self.Q_hp(T_tank, T_amb) for T_tank, T_amb in zip(solution.y[0], T_amb_interpolated)]
        Q_hp_total = np.trapz(Q_hp_values, t_eval)

        avg_cop = np.mean(self.cop_values) if self.cop_values else 0

        T_tank_values = solution.y[0] - 273.15
        time_values = solution.t

        return time_values, T_tank_values, Q_hp_total, avg_cop, self.cop_values

# Function to run the heat system simulation
def run_heat_system_simulation(Aw, Uw, Ar, Ur, T_amb_list, T_sp, U_cond, T_cond, U_tank, A_tank, c_t, A_cond, initial_tank_temp=318.15):
    heat_system = Heat_system(Aw, Uw, Ar, Ur, T_amb_list, T_sp, U_cond, T_cond, U_tank, A_tank, c_t, A_cond)
    return heat_system.solve_tank_temperature(initial_tank_temp)
