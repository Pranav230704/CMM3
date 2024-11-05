# -*- coding: utf-8 -*-
"""
Created on Tue Nov  5 13:27:43 2024

@author: Findlay
"""

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