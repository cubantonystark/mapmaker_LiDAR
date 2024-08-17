import tkinter as tk

def print_coordinates():
    latitude = latitude_entry.get()
    longitude = longitude_entry.get()
    altitude = altitude_entry.get()
    print("Latitude:", latitude)
    print("Longitude:", longitude)
    print("Altitude:", altitude)

# Create main window
root = tk.Tk()
root.title("Coordinates Input")

# Create labels and text entry widgets
latitude_label = tk.Label(root, text="Latitude:")
latitude_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
latitude_entry = tk.Entry(root)
latitude_entry.grid(row=0, column=1, padx=10, pady=5)

longitude_label = tk.Label(root, text="Longitude:")
longitude_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
longitude_entry = tk.Entry(root)
longitude_entry.grid(row=1, column=1, padx=10, pady=5)

altitude_label = tk.Label(root, text="Altitude:")
altitude_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
altitude_entry = tk.Entry(root)
altitude_entry.grid(row=2, column=1, padx=10, pady=5)

# Create continue button
continue_button = tk.Button(root, text="Continue", command=print_coordinates)
continue_button.grid(row=3, column=0, columnspan=2, padx=10, pady=10)

root.mainloop()