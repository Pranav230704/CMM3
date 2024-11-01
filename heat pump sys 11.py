# -*- coding: utf-8 -*-
"""
Created on Wed Oct  9 11:25:14 2024

@author: yisheng du
"""
import numpy as np
import yaml
from scipy.optimize import curve_fit
from datetime import datetime
from meteostat import Point, Hourly
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt
# Define the location (Edinburgh: 55.9533° N, 3.1883° W)
location = Point(55.9533, -3.1883)
# Set the time period for data retrieval
start = datetime(2023, 1, 1, 0) # Start time
end = datetime(2023, 1, 2, 0) # End time (24-hour period)
# Fetch hourly temperature data
data = Hourly(location, start, end)
data = data.fetch()
#print(data)

T_amb_list = data['temp'].tolist()
#print(T_amb_list)

#open cop yaml file
file_path1 = "C:\\Users\\Raymond M Rothschild\\Downloads\\heat_pump_cop_synthetic_full.yaml"
with open(file_path1,'r') as file :
    cop_yaml = yaml.safe_load(file)
#print(cop_yaml)
cop_temp = []
cop_cop = []

# pick out data from yam file
for i in cop_yaml['heat_pump_cop_data']:
    cop_temp.append(i['outdoor_temp_C'])
    cop_cop.append(i['COP_noisy'])
    
#print(cop_cop)
#rint(cop_temp)

class Heat_system:
    def __init__(self,Aw,Uw,Ar,Ur,T_amb_list,T_sp,U_cond,T_cond,U_tank,A_tank,c_t):#M_water,Ini_tank_temp,pump_critemp,Q_loss,U_tank,A_tank
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
        self.pump_on = False
        #self.M_water = M_water
        #self.Ini_tank_temp = Ini_tank_temp
        #self.pump_critemp = pump_critemp
        
    
    def Q_load(self):
        Q_loads = []
        for i, Tamb in enumerate(self.T_amb_list):
            #print(Tamb)
            Q_load = self.Aw*self.Uw*(Tamb + 273 - self.T_sp)+self.Ar*self.Ur*(Tamb + 273 - self.T_sp)
            Q_loads.append(Q_load)
    
        return Q_loads
    
    
    def cop(self,temp,a,b):
        init_temp = 60
        delta_T = [init_temp- i for i in cop_temp]
        return a + b/np.array(delta_T)
    popt, pcov = curve_fit(cop,cop_temp,cop_cop)
    a,b = popt[-2:]
    #print(a)
    #print(b)
    real_cop = []
    for i in range(len(T_amb_list)):
        real_cop.append(a + b/(T_amb_list[i] - 60))
        
    #print(real_cop)
        
    def Q_hp(self,T_tank):
        if T_tank >= 60+273.15:
            self.pump_on = False
        elif T_tank <= 40+273.15:
            self.pump_on = True
        if self.pump_on:
            #return  self.U_cond*(self.Aw + self.Ar)*(self.T_cond - T_tank)
            return  self.U_cond*self.A_tank*(self.T_cond - T_tank)
        else:
            return 0

    def tank_temperature_ode(self, t, T_tank):
        Q_hp = self.Q_hp(T_tank)
        # 确保t的索引不超过T_amb_list的范围
        #index = int(t/3600)
        Load = np.interp(t,np.linspace(0,86400,len(self.Q_load())),self.Q_load())
        #T_amb = self.T_amb_list[index] 
        T_amb = np.interp(t,np.linspace(0,86400,len(self.T_amb_list)),self.T_amb_list)
        
        #Q_loss = self.U_tank * self.A_tank * (T_tank - T_amb)
        Q_loss = self.U_tank * (T_tank - T_amb)
        # 返回温度变化率 dT/dt
        print(t)
        if self.pump_on:
            print("33333333333333")
            print(Q_hp)
            print(Load)
            print(Q_loss[0])
        dTdt = (Q_hp - Load - Q_loss[0]) / self.c_t
        #dTdt = (Q_hp - self.Q_load()[index] - Q_loss[0]) / self.c_t
        return dTdt

   # Solve_ivp 使用
    def solve_tank_temperature(self, initial_tank_temp, total_time=86400, time_points=1000):
       # 时间点划分
        t_eval = np.linspace(0, total_time, time_points)
       
       # 调用 solve_ivp 进行求解
        solution = solve_ivp(self.tank_temperature_ode, [0, total_time], [initial_tank_temp], t_eval=t_eval,method="RK45")
       
       # 提取结果
        T_tank_values = solution.y[0] - 273.15 # 水箱温度的解
        time_values = solution.t  # 时间点
       
        return time_values, T_tank_values
    
def main():
    #Aw = float(input("please enter wall area(Aw) in m^2:"))
    #Uw = float(input("please enter wall U-value(Uw) in W/m^2:"))
    #Ar = float(input("please enter roof area(Ar) in m^2:"))
    #Ur = float(input("please enter roof U-value(Ur) in W/m^2:"))
    #T_sp = float(input("please enter indoor setpoint temperature in K:"))
    #U_cond = float(input("please enter condenser overall heat transfer coefficient (U_cond) in W/m^2K:"))
    #T_cond = float(input("please enter condenser temperature (T_cond) in K:"))
    #U_tank = float(input("please enter tank heat loss coefficient (U_tank) in W/K:"))
    ##A_tank = float(input("please enter tank heat transfer area (A_tank) in m^2:"))
    #c_t = float(input("please enter total thermal capacity of the tank (c_t) in J/K:"))
    
    Aw = 132 #float(input("please enter wall area(Aw) in m^2:"))
    Uw =0.51 #float(input("please enter wall U-value(Uw) in W/m^2:"))
    Ar = 120#float(input("please enter roof area(Ar) in m^2:"))
    Ur = 0.18#float(input("please enter roof U-value(Ur) in W/m^2:"))
    T_sp = 293.15#float(input("please enter indoor setpoint temperature in K:"))
    U_cond = 300#float(input("please enter condenser overall heat transfer coefficient (U_cond) in W/m^2K:"))
    T_cond = 343.15#float(input("please enter condenser temperature (T_cond) in K:"))
    U_tank = 5#float(input("please enter tank heat loss coefficient (U_tank) in W/K:"))
    A_tank = 1.11#(input("please enter tank heat transfer area (A_tank) in m^2:"))
    c_t = 837200#float(input("please enter total thermal capacity of the tank (c_t) in J/K:"))

    heat_system = Heat_system(Aw,Uw,Ar,Ur,T_amb_list,T_sp,U_cond,T_cond,U_tank,A_tank,c_t)
    
    # 调用求解水箱温度的函数
    initial_tank_temp = 45 + 273.15  # assume T_tank initinal 45°C
    time_values, T_tank_values = heat_system.solve_tank_temperature(initial_tank_temp)
    
    # 打印结果
    #print(f"Time (hours): {time_values / 3600}")
    #print(f"Tank Temperature (K): {T_tank_values}")
    
    # plt figure
    plt.figure(figsize=(12, 6))
    plt.plot(time_values / 3600, T_tank_values)
    plt.xlabel('Time (hours)')
    plt.ylabel('Tank Temperature (K)')
    plt.title('Tank Temperature Over Time')
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    main()
 
   
