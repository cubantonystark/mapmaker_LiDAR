'''
Compile with pyinstaller MM_GUI.py --icon=gui_images/ARTAK_103_drk.ico --collect-all=pymeshlab --onedir --collect-all=open3d
Make sure to comment the line: subprocess.Popen(["python", "MM_pc2mesh.py"])
and uncomment: #subprocess.run(["MM_pc2mesh.exe"]) # Change to this when compiling .exe file
'''
import os, platform

if not os.path.exists('debug') and platform.system() == 'Windows':

    import win32gui, win32con
    #This snippet hides the console in non compiled scripts. Done for aesthetics
    this_program = win32gui.GetForegroundWindow()
    win32gui.ShowWindow(this_program, win32con.SW_HIDE)
     
import xml.etree.ElementTree as ET
import random, psutil, glob
from datetime import datetime
from PIL import Image
import shutil, webview
import open3d as o3d

'''
We will create the work folders on first run. This code serves as a check in case the one of the working folders gets
accidentaly deleted.
'''

dirs1 = ['ARTAK_MM/LOGS', 'ARTAK_MM/POST/Lidar', 'ARTAK_MM/DATA/Processing', 'ARTAK_MM/DATA/Generated_Mesh', 'ARTAK_MM/DATA/Generated_PointClouds', 'ARTAK_MM/DATA/Scan_Logs', 'ARTAK_MM/DATA/Imagery']

# cleanup any straggler status file in case of disgraceful exit of either recon script

if os.path.exists("exlogs.txt"):
    
    os.remove("exlogs.txt")
    
for dir in dirs1:
    
    if not os.path.exists(dir):
        os.makedirs(dir)

    else:
        continue

import sys, time, threading, win32file, subprocess, pymeshlab, requests
from bs4 import BeautifulSoup
from tkinter import filedialog, messagebox
import customtkinter
from CTkListbox import *
import tkinter as tk
from tkhtmlview import HTMLLabel
from pathlib import Path

sys.setrecursionlimit(1999999999)

customtkinter.set_appearance_mode("Dark")  # Modes: system (default), light, dark
customtkinter.set_default_color_theme("blue")  # Themes: blue (default), dark-blue, green

global once

once = 0

class ScrollableLabelButtonFrame(customtkinter.CTkScrollableFrame):
    def __init__(self, master, command=None, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)

        self.command = command
        self.radiobutton_variable = customtkinter.StringVar()
        self.label_list = []
        self.button_list = []

    def add_item(self, button_command=None, image=None, file=None, _time=None):
        # filename = os.listdir(item)
        #  print ("filename = " + filename)
        path = Path(file)
        if _time is None:
            for each_file in os.listdir(path.parent.absolute()):
                if "zip" in each_file:
                    _time = str(each_file).split(".")[0]
                    #print("time =" + str(_time))
        #print("file = " + file)
        label = customtkinter.CTkLabel(self, text=_time, image=image, compound="left", padx=5, anchor="w")
        button = customtkinter.CTkButton(self, text="Open", width=100, height=24)
        #print("button command = " + str(button_command))
        #print(file)
        if button_command is not None:
            button.configure(command=lambda: self.command(button_command))
        label.grid(row=len(self.label_list), column=0, pady=(0, 10), sticky="w")
        button.grid(row=len(self.button_list), column=1, pady=(0, 10), padx=5)
        self.label_list.append(label)
        self.button_list.append(button)

    def remove_item(self, item):
        for label, button in zip(self.label_list, self.button_list):
            if item == label.cget("text"):
                label.destroy()
                button.destroy()
                self.label_list.remove(label)
                self.button_list.remove(button)
                return

    def remove_all(self):
        for label, button in zip(self.label_list, self.button_list):
            label.destroy()
            button.destroy()
class App(customtkinter.CTk):

    def __init__(self):
        super().__init__()
        self.once = once
        self.iconbitmap(default='gui_images/ARTAK_103.ico')
        self.title("ARTAK 3D Map Maker || LiDAR || v1.0.8")
        self.geometry("1650x465")
        self.protocol('WM_DELETE_WINDOW', self.terminate_all)
        self.resizable(False, False)

        # set grid layout 1x2
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # load images with light and dark mode image
        image_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "gui_images")
        self.logo_image = customtkinter.CTkImage(
            light_image=Image.open("gui_images/logo_light_scheme.png"),
            dark_image=Image.open("gui_images/logo_dark_scheme.png"),
            size=(100, 33))
        self.large_test_image = customtkinter.CTkImage(Image.open("gui_images/large_test_image.png"),
                                                       size=(500, 150))
        self.image_icon_image = customtkinter.CTkImage(Image.open("gui_images/image_icon_light.png"),
                                                       size=(20, 20))
        self.home_image = customtkinter.CTkImage(light_image=Image.open("gui_images/home_dark.png"),
                                                 dark_image=Image.open("gui_images/home_light.png"),
                                                 size=(20, 20))
        self.chat_image = customtkinter.CTkImage(light_image=Image.open("gui_images/chat_dark.png"),
                                                 dark_image=Image.open("gui_images/chat_light.png"),
                                                 size=(20, 20))
        self.add_user_image = customtkinter.CTkImage(
            light_image=Image.open(os.path.join("gui_images/add_user_dark.png")),
            dark_image=Image.open(os.path.join("gui_images/add_user_light.png")), size=(20, 20))
        
        self.add_scanner_image = customtkinter.CTkImage(
            light_image=Image.open(os.path.join("gui_images/folder_open_dark.png")),
            dark_image=Image.open(os.path.join("gui_images/folder_open_white.png")), size=(20, 20))        

        # create fourth frame
        self.fourth_frame = customtkinter.CTkScrollableFrame(self, corner_radius=0, fg_color="transparent")
        
        # create navigation frame
        self.navigation_frame = customtkinter.CTkFrame(self, corner_radius=0)
        self.navigation_frame.grid(row=0, column=0, sticky="nsew")
        self.navigation_frame.grid_rowconfigure(5, weight=1)

        self.navigation_frame_label = customtkinter.CTkLabel(self.navigation_frame, text="  3D Map Maker || LiDAR",
                                                             image=self.logo_image,
                                                             compound="left",
                                                             font=customtkinter.CTkFont(size=15, weight="bold"))
        self.navigation_frame_label.grid(row=0, column=0, padx=20, pady=20)

        self.home_button = customtkinter.CTkButton(self.navigation_frame, corner_radius=0, height=40, border_spacing=10,
                                                   text="Home",
                                                   fg_color="transparent", text_color=("gray10", "gray90"),
                                                   hover_color=("gray70", "gray30"),
                                                   image=self.home_image, anchor="w", command=self.home_button_event)
        self.home_button.grid(row=1, column=0, sticky="ew")
        
        self.frame_2_button = customtkinter.CTkButton(self.navigation_frame, corner_radius=0, height=10,
                                                      border_spacing=10, text="System Logs",
                                                      fg_color="transparent", text_color=("gray10", "gray90"),
                                                      hover_color=("gray70", "gray30"),
                                                      image=self.chat_image, anchor="w",
                                                      command=self.frame_2_button_event)
        self.frame_2_button.grid(row=2, column=0, sticky="ew")            

        self.frame_4_button = customtkinter.CTkButton(self.navigation_frame, corner_radius=0, height=10,
                                                      border_spacing=10, text="Settings",
                                                      fg_color="transparent", text_color=("gray10", "gray90"),
                                                      hover_color=("gray70", "gray30"),
                                                      image=self.add_user_image, anchor="w",
                                                      command=self.frame_4_button_event)
        self.frame_4_button.grid(row=3, column=0, sticky="ew") 

        # create home frame
        
        self.home_frame = customtkinter.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.home_frame.grid_columnconfigure(0, weight=1)

        self.home_frame_large_image_label = customtkinter.CTkLabel(self.home_frame, text="",
                                                                   image=self.large_test_image)

        self.auto_process_sd_frame = customtkinter.CTkFrame(self)
        self.auto_process_sd_var = customtkinter.BooleanVar()
        self.auto_process_sd_var.set(value=False)

        ###

        # region settings frame
        
        ## Only Generate Raw OBJ
        
        self.raw_obj = customtkinter.BooleanVar()
        self.raw_obj.set(False)
    
        self.auto_open_text = customtkinter.CTkLabel(self.fourth_frame, text="Generate Standalone Mesh Only")
        self.auto_open_text.grid(row=0, column=0, padx=20, pady=10)
        self.auto_open_switch = customtkinter.CTkSwitch(self.fourth_frame, text="", variable=self.raw_obj)
        self.auto_open_switch.grid(row=0, column=1, padx=20, pady=10)        
        
        ## Server Settings
        self.home_frame_server = customtkinter.CTkLabel(self.fourth_frame, text="Select ARTAK Server")
        self.home_frame_server.grid(row=2, column=0, padx=20, pady=10)    
        
        self.server_button_frame = customtkinter.CTkFrame(self)
        self.server_var = customtkinter.StringVar()
        
        self.local_radio_button = customtkinter.CTkRadioButton(self.fourth_frame, text="Local",
                                                                   variable=self.server_var,
                                                                   value="http://eoliancluster.local/")
        self.local_radio_button.grid(row=2, column=1, padx=20, pady=10)        
    
        self.cloud_radio_button = customtkinter.CTkRadioButton(self.fourth_frame, text="Cloud",
                                                                   variable=self.server_var,
                                                                   value="https://esp.eastus2.cloudapp.azure.com/")
        self.cloud_radio_button.grid(row=2, column=2, padx=20, pady=10)
    
        ## Local ARTAK Server
    
        self.local_server_label = customtkinter.CTkLabel(self.fourth_frame, text="Custom ARTAK Server")
        self.local_server_label.grid(row=4, column=0, padx=20, pady=10, sticky="ew")
        
        self.local_server_ip_entry = customtkinter.CTkEntry(self.fourth_frame, width = 300)
        self.local_server_ip_entry.grid(row=4, column=1, padx = 20, columnspan = 2, sticky="ew")
        
        ## Mesh Type
        
        self.home_frame_button_4 = customtkinter.CTkLabel(self.fourth_frame, text="Generated Map type")
        self.home_frame_button_4.grid(row=6, column=0, padx=20, pady=10)

        self.button_frame = customtkinter.CTkFrame(self)
        self.mesh_from_pointcloud_type_var = customtkinter.StringVar()
        self.mesh_from_pointcloud_type_var.set("m")
        
        self.obj_radio_button = customtkinter.CTkRadioButton(self.fourth_frame, text="Legacy",
                                                                     variable=self.mesh_from_pointcloud_type_var,
                                                                     value="m")
        self.obj_radio_button.grid(row=6, column=1, padx=20, pady=10)

        self.tiles_radio_button2 = customtkinter.CTkRadioButton(self.fourth_frame, text="Tiled Mesh",
                                                                variable=self.mesh_from_pointcloud_type_var,
                                                                value="tm")
        self.tiles_radio_button2.grid(row=6, column=2, padx=20, pady=10)   
        
        self.tiles_radio_button3 = customtkinter.CTkRadioButton(self.fourth_frame, text="Tiled PointCloud (Experimental)",
                                                                variable=self.mesh_from_pointcloud_type_var,
                                                                value="tpc") #Thanks Matt!
        self.tiles_radio_button3.grid(row=6, column=3, padx=20, pady=10)          
        
        ## Appearance Settings
        
        self.apperance_mode_label = customtkinter.CTkLabel(self.fourth_frame, text="App Screen Mode")
        self.apperance_mode_label.grid(row=8, column=0, padx=20, pady=20, sticky="s")

        self.appearance_mode_menu = customtkinter.CTkOptionMenu(self.fourth_frame,
                                                                values=["Dark", "Light"],
                                                                command=self.change_appearance_mode_event)
        self.appearance_mode_menu.grid(row=8, column=1, padx=20, pady=20, sticky="nsew", columnspan=2)        
        
        ## Auto Open
        
        self.auto_open_var = customtkinter.BooleanVar()
        self.auto_open_var.set(True)
    
        self.auto_open_text = customtkinter.CTkLabel(self.fourth_frame, text="Auto open Map after Completion?")
        self.auto_open_text.grid(row=10, column=0, padx=20, pady=10)
        self.auto_open_switch = customtkinter.CTkSwitch(self.fourth_frame, text="", variable=self.auto_open_var)
        self.auto_open_switch.grid(row=10, column=1, padx=20, pady=10) 
        
        ## Auto upload after completion
        
        self.upload_label = customtkinter.CTkLabel(self.fourth_frame, text="Upload After Completion")
        self.upload_label.grid(row=12, column=0, padx=20, pady=10)

        self.upload_var = customtkinter.StringVar()
        self.upload_var.set("N")

        self.upload_yes_radio_button = customtkinter.CTkRadioButton(self.fourth_frame, text="N", variable=self.upload_var,
                                                             value="N")
        self.upload_yes_radio_button.grid(row=12, column=1, padx=20, pady=10)

        self.upload_no_radio_button = customtkinter.CTkRadioButton(self.fourth_frame, text="Y", variable=self.upload_var,
                                                            value="Y")
        self.upload_no_radio_button.grid(row=12, column=2, padx=20, pady=10)         
        
        ## Delete after upload
        
        self.delete_after_transfer_var = customtkinter.StringVar()
        self.delete_after_transfer_var.set("N")
        
        self.radio_label2 = customtkinter.CTkLabel(self.fourth_frame, text="Delete After Upload")
        self.radio_label2.grid(row=14, column=0, padx=20, pady=10)

        self.yes_radio_button = customtkinter.CTkRadioButton(self.fourth_frame, text="N", variable=self.delete_after_transfer_var,
                                                             value="N")
        
        self.yes_radio_button.grid(row=14, column=1, padx=20, pady=10)

        self.no_radio_button = customtkinter.CTkRadioButton(self.fourth_frame, text="Y", variable=self.delete_after_transfer_var,
                                                            value="Y")
        self.no_radio_button.grid(row=14, column=2, padx=20, pady=10)     
                
        ## Save Button
        
        self.save_settings = customtkinter.CTkButton(self.fourth_frame, text="Save Settings", command=self.read_settings_and_save,
                                                        state="normal")
        self.save_settings.grid(row=21, column=1, padx=20, pady=10)        

        ## endregion
        
        # Load PointCloud region
        
        self.file_origin = customtkinter.StringVar()
        self.file_origin.set("L")
        
        self.local_radio_button = customtkinter.CTkRadioButton(self.home_frame, text="Local Drive", variable=self.file_origin,
                                                             value="L")
        
        self.local_radio_button.place(x = 50, y = 25)

        self.exyn_sensor_radio_button = customtkinter.CTkRadioButton(self.home_frame, text="Exyn Sensor", variable=self.file_origin,
                                                            value="R")
        
        self.exyn_sensor_radio_button.place(x = 225, y = 25)        
        
        self.lat_label = customtkinter.CTkLabel(self.home_frame, text="Latitude")
        self.lat_label.place(x = 50, y = 75)
        
        self.lat_entry = customtkinter.CTkEntry(self.home_frame, width = 150)
        self.lat_entry.place(x = 50, y = 100)
        
        self.lon_label = customtkinter.CTkLabel(self.home_frame, text="Longitude")     
        self.lon_label.place(x = 225, y = 75)
        
        self.lon_entry = customtkinter.CTkEntry(self.home_frame, width = 150)
        self.lon_entry.place(x = 225, y = 100)        
        
        self.elev_label = customtkinter.CTkLabel(self.home_frame, text="Elevation")     
        self.elev_label.place(x = 400, y = 75)
        
        self.elev_entry = customtkinter.CTkEntry(self.home_frame, width = 150)
        self.elev_entry.place(x = 400, y = 100)    
        
        self.lat_entry.insert(0, "0.0")
        self.lon_entry.insert(0, "0.0")
        self.elev_entry.insert(0, "0.0")
        
        self.browse_button_pc = customtkinter.CTkButton(self.home_frame, text="Browse", command=self.pre_processing, state="normal")
        self.browse_button_pc.place(x = 575, y = 100)  
        
        # endregion

        # create second frame
        
        self.second_frame = customtkinter.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.second_frame.grid_rowconfigure(0, weight=1)  # configure grid system
        self.second_frame.grid_columnconfigure(0, weight=1)

        self.output_text2 = customtkinter.CTkTextbox(self.second_frame, height=400)
        self.output_text2.grid(row=0, column=0, padx=5, pady=5, sticky="nsew", columnspan=4)

        # create third frame
        self.third_frame = customtkinter.CTkScrollableFrame(self, corner_radius=0, fg_color="transparent")
        
        # select default frame
        self.select_frame_by_name("home")
        self.list_of_projects = []
        self.scrollable_label_button_frame = ScrollableLabelButtonFrame(master=self, width=300,
                                                                        command=self.label_button_frame_event,
                                                                        corner_radius=0)
        self.scrollable_label_button_frame.grid(row=0, column=2, padx=0, pady=0, sticky="nsew")
        self.list_of_objs = []
        
        self.list_of_progress_bars = []
        self.local_server_ip = ""
        
        if not os.path.exists("settings.cfg"):
            self.read_settings_and_save()
        else:
            self.read_settings_and_update()
            
        log_entry = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))+" INFO App Startup Complete.\r"
        
        self.write_to_runtime_log(log_entry)      
    
    def write_to_runtime_log(self, log_entry):
        
        with open("ARTAK_MM/LOGS/runtime.log", "w") as runtimelog:
            runtimelog.write(str(log_entry.strip()))
        return
    
    def read_from_exyn_runtime_log(self):
        
        cmd = 'wsl --user mapmaker -e bash -c "tail -1 /home/mapmaker/exyn/runtime.log && exit; exec bash"'
        result = subprocess.check_output(cmd, shell = True)
        result = result.decode("utf-8")
        return result
    
    def read_from_runtime_log(self):
        
        with open("ARTAK_MM/LOGS/runtime.log", "r") as runtimelog:
            log_entry = runtimelog.read().strip()
        return log_entry

    def add_to_log_screen(self):
        
        prev_log_entry = ""
        
        while True:
            
            log_entry = self.read_from_runtime_log().rstrip()
            
            if prev_log_entry == log_entry:
                pass
            
            elif '_io.TextIOWrapper name' in log_entry:
                    pass
                
            elif 'None' in log_entry:
                    pass 
                
            else:
                
                self.output_text2.insert(tk.END, str("\n"+log_entry))
                self.output_text2.see(tk.END)
                
            prev_log_entry = log_entry
            time.sleep(0.05) 
            
    def add_to_log_screen_from_exyn_log(self):
        
        prev_log_entry_exyn = ""
        
        while True:

            log_entry_exyn = self.read_from_exyn_runtime_log()
            
            if prev_log_entry_exyn == log_entry_exyn:
                pass
                
            else:
                
                self.output_text2.insert(tk.END, str("\n"+log_entry_exyn))
                self.output_text2.see(tk.END)
                
            prev_log_entry_exyn = log_entry_exyn
        
    def read_settings_and_save(self):
        
        config = []
        
        raw_obj = self.raw_obj.get()
        server_addr = self.server_var.get()
        resulting_mesh_type = self.mesh_from_pointcloud_type_var.get()
        auto_open = self.auto_open_var.get()
        upload_yn = self.upload_var.get()
        del_after_xfer = self.delete_after_transfer_var.get()
        
        config.append(raw_obj)
        config.append(server_addr)
        config.append(resulting_mesh_type)
        config.append(auto_open)
        config.append(upload_yn)
        config.append(del_after_xfer)
        
        self.local_server_ip_entry.delete(0, tk.END)
        self.local_server_ip_entry.insert(0, self.server_var.get())          
        
        with open("settings.cfg", "w") as settings:
            
            for item in config:
                settings.write(str(item)+"\r")
        
        return
    
    def read_settings_and_update(self):
        
        with open("settings.cfg", "r") as settings:
            cfg = settings.readlines()
            
        raw_obj, server_addr, resulting_mesh_type, auto_open, upload_yn, del_after_xfer = cfg
        
        self.raw_obj.set(raw_obj.strip())
        self.server_var.set(server_addr.strip())
        self.mesh_from_pointcloud_type_var.set(resulting_mesh_type.strip())
        self.auto_open_var.set(auto_open.strip())
        self.upload_var.set(upload_yn.strip())
        self.delete_after_transfer_var.set(del_after_xfer.strip())
        
        self.local_server_ip_entry.delete(0, tk.END)
        self.local_server_ip_entry.insert(0, self.server_var.get())        
        
        return   
    
    def get_remote_dir_listing(self, url):
        
        try:
        
            response = requests.get(url, timeout = 3)
            
            # Check if the request was successful
            
            if response.status_code == 200:
                # Parse the HTML content
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find all 'a' tags which represent links
                links = soup.find_all('a')
                
                # Extract the file names and folder names
                files = []
                folders = []
                for link in links:
                    href = link.get('href')
                    # Ignore parent directory link and current directory link
                    if href != '../' and href != './':
                        if href.endswith('/'):
                            # If it ends with '/', it's a folder
                            folders.append(href)
                        else:
                            # Otherwise, it's a file
                            files.append(href)
                
                with open("exlogs.txt", "w") as exlogfile:
            
                    for file in files:
                        
                        if '.ex' in file:
                            
                            exlogfile.write(str(file+"\r")) 
                            
                self.display_remote_dir_listing()
                            
            else:
                
                # If the request was not successful, print an error message
                print("Error:", response.status_code)

                return
            
        except (TimeoutError, requests.exceptions.ConnectionError):
            
            messagebox.showerror('ARTAK 3D Map Maker', 'Could not retrieve remote files. \nPlease make sure you are connected to the device and try again.')
            
            self.browse_button_pc.configure(state='normal')

            return
        
    def display_remote_dir_listing(self):
        
        def download_threaded(selected_option):
            
            remote_window.forget(remote_window)
            
            with open("ARTAK_MM/LOGS/status.log", "w") as status:
                status.write("running")                 
            
            if os.path.exists("ARTAK_MM/DATA/Scan_logs/"+selected_option):
                os.unlink("ARTAK_MM/DATA/Scan_logs/"+selected_option)
            
            log_entry = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))+" INFO Downloading Exlog "+selected_option+".\r"
            self.write_to_runtime_log(log_entry)
    
            url = "http://192.168.2.1:8080/xfiles/"+selected_option
            response = requests.get(url, stream = True)
            
            total_size = int(response.headers.get('content-length', 0))
            block_size = 1048576
            count = 1048576
            
            file_name, extension = os.path.splitext(selected_option)
            
            file_name = file_name.replace(".", '_')
            
            new_pc_file = file_name+extension
            
            with open("ARTAK_MM/DATA/Scan_logs/"+new_pc_file, "wb") as exlog_to_save:
                
                for data in response.iter_content(block_size):
    
                    count += block_size
                    exlog_to_save.write(data)
                    percentage = int(((count/total_size)*100))
                    log_entry = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))+" INFO "+str(percentage)+"% of "+ str(selected_option)+" downloaded."
                    self.write_to_runtime_log(log_entry)
               
            log_entry = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))+" INFO Exlog download complete.\r"
            self.write_to_runtime_log(log_entry)
            
            with open("ARTAK_MM/LOGS/status.log", "w") as status:
                status.write("done")                     
    
            fullpath = "ARTAK_MM/DATA/Scanner_Logs/"+selected_option
            
            with open("ARTAK_MM/LOGS/runtime.log", "w") as runtime:
                
                runtime.write(str(fullpath)) 
                
            self.listbox.bindtags((self.listbox, 'Listbox', '.', "all")) 
            
            download_type = self.download_type.get()
            
            print(download_type)
            
            if download_type == "dp":
                
                fullpath = "ARTAK_MM/DATA/Scan_logs/"+selected_option
                
                with open("ARTAK_MM/LOGS/runtime.log", "w") as runtime:
                    
                    runtime.write(str(fullpath))
        
                subprocess.Popen(["python", "MM_pc2mesh.py"])                
                
        def download_exlog(event):
            
            #self.download_type.set("d")
            
            self.listbox.bindtags((self.listbox, remote_window, "all"))
    
            selection = event.widget.curselection()                
    
            if len(selection) == 0:
                
                self.browse_button_pc.configure(state='normal')
    
                return
    
            else:
    
                index = selection[0]
    
                selected_option = event.widget.get(index)
                
            threading.Thread(target= lambda: download_threaded(selected_option)).start() 

        from tkinter import Tk
  
        remote_window = tk.Toplevel()
        remote_window.title("Available scans")
        remote_window.geometry("470x450")
        remote_window.configure(bg="gray25")
        remote_window.resizable(False, False)
        scrollbar = tk.Scrollbar(remote_window)
        scrollbar.grid(row=0, column=1, sticky='nsw') 

        self.listbox = tk.Listbox(remote_window, width=40, height = 15, font = customtkinter.CTkFont(size=18), selectmode=tk.BROWSE, exportselection=False, yscrollcommand=scrollbar.set)
        self.listbox.grid(row=0, column=0, sticky = 'nse')  

        scrollbar.config(command=self.listbox.yview)   

        self.download_type = customtkinter.StringVar()
        self.download_type.set("dp")

        self.local_radio_button = customtkinter.CTkRadioButton(remote_window, text="Download Only", variable=self.download_type,
                                                                       value="d")

        self.local_radio_button.place(x = 10, y = 305)

        self.exyn_sensor_radio_button = customtkinter.CTkRadioButton(remote_window, text="Download and Process", variable=self.download_type,
                                                                             value="dp")

        self.exyn_sensor_radio_button.place(x = 200, y = 305)                 

        self.listbox.bind('<<ListboxSelect>>', download_exlog)

        with open("exlogs.txt") as exlogs_list:

            options = exlogs_list.readlines()

        self.listbox.delete(0,tk.END)

        for option in options:

            self.listbox.insert(tk.END, option.rstrip())   
            
    def pre_processing(self):
        
        with open("settings.cfg", "r") as settings:
            cfg = settings.readlines()
            
        raw_obj, server_addr, resulting_mesh_type, auto_open, upload_yn, del_after_xfer = cfg
        
        self.raw_obj.set(raw_obj.strip())
        self.server_var.set(server_addr.strip())
        self.mesh_from_pointcloud_type_var.set(resulting_mesh_type.strip())
        self.auto_open_var.set(auto_open.strip())
        self.upload_var.set(upload_yn.strip())
        self.delete_after_transfer_var.set(del_after_xfer.strip())
        
        self.local_server_ip_entry.delete(0, tk.END)
        self.local_server_ip_entry.insert(0, self.server_var.get())         
        
        self.browse_button_pc.configure(state='disabled')
        
        file_origin = self.file_origin.get()
        lat = self.lat_entry.get()
        lon = self.lon_entry.get()
        elev = self.elev_entry.get()
        
        resulting_mesh_type = resulting_mesh_type.rstrip()
        
        with open("coords.txt", "w") as coords:
            
            coords.write(str(lat)+","+str(lon)+","+str(elev))  
            
        if file_origin == "R":
            
            url = "http://192.168.2.1:8080/xfiles/"
            self.get_remote_dir_listing(url)
            
        else:
            
            if resulting_mesh_type == "tpc":
                
                description = "PointClouds"
                extensions = "*.ply; *.e57; *.pts"
                
            else:
                
                description = "ExLogs, PointClouds, Standalone OBJs"
                extensions = "*.ply;*.pts;*.e57;*.ex;*.obj"
            
            fullpath = filedialog.askopenfile(filetypes=((description, extensions), ("All files", "*.*")))
            fullpath = str(fullpath)

            if len(fullpath) == 4:
                
                self.browse_button_pc.configure(state='normal')
                return
            
            else:

                with open("ARTAK_MM/LOGS/runtime.log", "w") as runtime:
                    
                    runtime.write(str(fullpath))
        
                subprocess.Popen(["python", "MM_pc2mesh.py"])            
    
    def terminate_all(self):
        
        # This will create a file in the logs folder that will signal we are closing shop
        
        with open(os.getcwd() + "/ARTAK_MM/LOGS/kill.mm", "w") as killer:
            pass
        
        if os.path.exists("ARTAK_MM/LOGS/status.log"):
            os.remove("ARTAK_MM/LOGS/status.log")
            
        os.remove(os.getcwd() + "/ARTAK_MM/LOGS/kill.mm")
        os.system('@taskkill /im python.exe /F >nul 2>&1')
        os.system('@taskkill /im MM_pc2mesh.exe /F >nul 2>&1')
        os.system('@taskkill /im wsl.exe /F >nul 2>&1')   
        os.system('@taskkill /im Obj2Tiles.exe /F >nul 2>&1')
            
        current_system_pid = os.getpid()

        ThisSystem = psutil.Process(current_system_pid)
        ThisSystem.terminate()
        
    def delete_all_source_data(self):
        directory = os.path.join(os.getcwd(), 'ARTAK_MM/DATA/Raw_Images/UNZIPPED')
        for f in os.listdir(directory):
            os.remove(os.path.join(directory, f))

    def open_pc_folder(self):

        cmd = os.getcwd() + "/ARTAK_MM/DATA/PointClouds"
        os.startfile(cmd)

    def display_activity_on_pc_recon(self):

        # will check if recon is running. should it be running, the 'Browse' button is disabled'

        self.progressbar_pc = customtkinter.CTkProgressBar(self.home_frame)
        
        while True:
            
            try:
                
                with open('ARTAK_MM/LOGS/status.log') as status:
                    status_finished = status.read()    
                    
                if 'running' in status_finished:
                    
                    self.browse_button_pc.configure(state='disabled')
                    self.exyn_sensor_radio_button.configure(state='disabled')
                    self.local_radio_button.configure(state='disabled')
                    self.lat_entry.configure(state='disabled')
                    self.lon_entry.configure(state='disabled')
                    self.elev_entry.configure(state='disabled')
                    
                    #self.progressbar_pc.grid(row=8, column=2, padx=20, pady=10, sticky="ew")
                    self.progressbar_pc.place(x = 740, y = 110)
                    self.progressbar_pc.configure(mode="determinate", progress_color="green")
                    self.progressbar_pc.set(0)
                    self.progressbar_pc.start()   
                    
                elif 'done' in status_finished:
                    
                    self.browse_button_pc.configure(state='normal')
                    self.exyn_sensor_radio_button.configure(state='normal')
                    self.local_radio_button.configure(state='normal')                    
                    self.lat_entry.configure(state='normal')
                    self.lon_entry.configure(state='normal')
                    self.elev_entry.configure(state='normal')                    
                    self.progressbar_pc.stop()
                    self.progressbar_pc.configure(progress_color="green")
                    self.progressbar_pc.set(1)

                    if self.once == 1:
                        
                        pass
                    
                    else:
                    
                        app.find_folders_with_obj_once()
                    
                elif 'error' in status_finished:
                    
                    self.browse_button_pc.configure(state='normal')
                    self.lat_entry.configure(state='normal')
                    self.lon_entry.configure(state='normal')
                    self.elev_entry.configure(state='normal')                     
                    self.progressbar_pc.stop()
                    self.progressbar_pc.configure(progress_color="red")
                    self.progressbar_pc.set(1)   
                    
                    self.listbox.bindtags((self.listbox, 'Listbox', '.', "all"))
                
            except FileNotFoundError:
                pass         
                
            time.sleep(3)

    def label_button_frame_event(self, item):
        self.open_obj(item)

    class TextRedirector:
        def __init__(self, widget, tag="stdout"):
            self.widget = widget
            self.tag = tag

        def write(self, str):
            self.widget.insert(tk.END, str, (self.tag,))
            self.widget.see(tk.END)

    def find_folders_with_obj(self):

        previous_file_count = 0

        while True:
            current_file_count = 0
            directory = ["ARTAK_MM/POST/Lidar"]
            for dirs in directory:
                current_file_count += len(os.listdir(os.path.join(os.getcwd(), dirs)))
            if current_file_count != previous_file_count:
                directory = os.getcwd() + "/ARTAK_MM/POST"
                self.list_of_objs = []
                for root, dirs, files in os.walk(directory):
                    if "Model" in dirs:
                        output_model_folder = os.path.join(root, "Model")
                        obj_files = [file for file in os.listdir(output_model_folder) if file.endswith(".obj")]
                        ply_files = [file for file in os.listdir(output_model_folder) if file.endswith(".ply")]
                        
                        if obj_files:
                            #print(f"Found Preprocessed folder with OBJ file(s): {output_model_folder}")
                            #print("OBJ files:")
                            #for obj_file in obj_files:
                                #print(os.path.join(output_model_folder, obj_file))
                            self.list_of_objs.append(output_model_folder)
                            self.scrollable_label_button_frame.update()
                            
                        if ply_files:
                            #print(f"Found Preprocessed folder with OBJ file(s): {output_model_folder}")
                            #print("OBJ files:")
                            #for obj_file in obj_files:
                                #print(os.path.join(output_model_folder, obj_file))
                            self.list_of_objs.append(output_model_folder)
                            self.scrollable_label_button_frame.update()   
                            
                self.scrollable_label_button_frame = ScrollableLabelButtonFrame(master=self, width=340,
                                                                                command=self.label_button_frame_event,
                                                                                corner_radius=0)
                self.scrollable_label_button_frame.grid(row=0, column=2, padx=0, pady=0, sticky="nsew")
                for each_item in self.list_of_objs:  # add items with images
                    self.scrollable_label_button_frame.add_item(file=each_item, button_command=each_item)
            else:
                pass
            previous_file_count = current_file_count
            time.sleep(5)

    def find_folders_with_obj_once(self):
        
        self.once = 1
        
        previous_file_count = 0
        current_file_count = 0
        directory = ["ARTAK_MM/POST/Lidar"]
        for dirs in directory:
            current_file_count += len(os.listdir(os.path.join(os.getcwd(), dirs)))
        if current_file_count != previous_file_count:
            directory = os.getcwd() + "/ARTAK_MM/POST/Lidar"
            self.list_of_objs = []
            for root, dirs, files in os.walk(directory):
                if "Model" in dirs:
                    output_model_folder = os.path.join(root, "Model")
                    obj_files = [file for file in os.listdir(output_model_folder) if file.endswith(".obj")]
                    ply_files = [file for file in os.listdir(output_model_folder) if file.endswith(".ply")]
                    
                    if obj_files:
                        #print(f"Found Preprocessed folder with OBJ file(s): {output_model_folder}")
                        #print("OBJ files:")
                        #for obj_file in obj_files:
                            #print(os.path.join(output_model_folder, obj_file))
                        self.list_of_objs.append(output_model_folder)
                        self.scrollable_label_button_frame.update()
                        
                    if ply_files:
                        #print(f"Found Preprocessed folder with OBJ file(s): {output_model_folder}")
                        #print("OBJ files:")
                        #for obj_file in obj_files:
                            #print(os.path.join(output_model_folder, obj_file))
                        self.list_of_objs.append(output_model_folder)
                        self.scrollable_label_button_frame.update()                        
                    
            self.scrollable_label_button_frame = ScrollableLabelButtonFrame(master=self, width=340,
                                                                            command=self.label_button_frame_event,
                                                                            corner_radius=0)
            self.scrollable_label_button_frame.grid(row=0, column=2, padx=0, pady=0, sticky="nsew")
            for each_item in self.list_of_objs:  # add items with images
                self.scrollable_label_button_frame.add_item(file=each_item, button_command=each_item)
        else:
            pass
        
        previous_file_count = current_file_count

        return

    def open_obj(self, path):
        
        if 'tpc_' in path:
            
            model_name = 'tpc_Model.ply'
            path = os.path.join(path, model_name)
            
            ply_point_cloud = o3d.data.PLYPointCloud()
            pcd = o3d.io.read_point_cloud(path)
            
            # This is the preview step
            o3d.visualization.draw_geometries([pcd],
                                                window_name=str('ARTAK 3D Map Maker || LiDAR Edition'),
                                                width=1280,
                                                height=900,
                                                zoom=0.32000000000000001,
                                                front=[-0.34267508672450531, 0.89966482743414444, 0.27051244558475285],
                                                lookat=[-15.934802105738544, -4.9954584521228949, 1.4543439424505489],
                                                up=[0.095768108125702828, -0.25299355589613992, 0.96271632900925208])
            return            
        
        if 'm_' in path:
            
            texture_name = 'm_texture.png'
            model_name = 'm_Model.obj'
            
        if 'tm_' in path:
            
            texture_name = 'tm_texture.png'
            model_name = 'tm_Model.obj'            
        
        albedo_name = os.path.join(path, texture_name)
        path = os.path.join(path, model_name)
        model_name = path
        
        model = o3d.io.read_triangle_mesh(model_name)
        material = o3d.visualization.rendering.MaterialRecord()
        #material.shader = "defaultLit"
        
        material.albedo_img = o3d.io.read_image(albedo_name)

        o3d.visualization.draw([{"name": "Model", "geometry": model, "material": material}], title = "ARTAK 3D Map Maker || LiDAR Edition", bg_color = [0,0,0,0], show_skybox = False, actions = None, width = 1280, height = 900)
        
        return
    
    def open_obj_new(self, path):
        print("opening obj > " + path)
        subprocess.Popen(['start', ' ', path], shell=True)

    def select_frame_by_name(self, name):
        # set button color forv selected button
        self.home_button.configure(fg_color=("gray75", "gray25") if name == "home" else "transparent")
        self.frame_4_button.configure(fg_color=("gray75", "gray25") if name == "frame_4" else "transparent")

        # show selected frame
        if name == "home":
            self.home_frame.grid(row=0, column=1, sticky="nsew")
        else:
            self.home_frame.grid_forget()
        if name == "frame_2":
            self.second_frame.grid(row=0, column=1, sticky="nsew")
        else:
            self.second_frame.grid_forget()
        if name == "frame_3":
            self.third_frame.grid(row=0, column=1, sticky="nsew")
        else:
            self.third_frame.grid_forget()
        if name == "frame_4":
            self.fourth_frame.grid(row=0, column=1, sticky="nsew")       
        else:
            self.fourth_frame.grid_forget()

    def home_button_event(self):
        self.select_frame_by_name("home")

    def frame_2_button_event(self):
        self.select_frame_by_name("frame_2")

    def frame_3_button_event(self):
        self.select_frame_by_name("frame_3")

    def frame_4_button_event(self):
        self.select_frame_by_name("frame_4")

    def change_appearance_mode_event(self, new_appearance_mode):
        customtkinter.set_appearance_mode(new_appearance_mode)
class StatusObject:

    def __init__(self, label, image_icon, name_entry_field, progress_bar):
        self.label = label
        self.image_icon = image_icon
        self.name_entry_field = name_entry_field
        self.progress_bar = progress_bar

if __name__ == "__main__":

    if os.path.exists("ARTAK_MM/LOGS/pc_type.log"):
        os.remove("ARTAK_MM/LOGS/pc_type.log")
        
    if os.path.exists("ARTAK_MM/LOGS/status.log"):
        os.remove("ARTAK_MM/LOGS/status.log")
        
    if os.path.exists("\\\wsl.localhost\\Ubuntu-22.04\\home\\mapmaker\\exyn\\runtime.log"):
        os.remove("\\\wsl.localhost\\Ubuntu-22.04\\home\\mapmaker\\exyn\\runtime.log")

    app = App()
    
    cmd = 'wsl --user mapmaker -e bash -c "touch /home/mapmaker/exyn/runtime.log && exit; exec bash"'
    os.system(cmd)
    
    threading.Thread(target=app.find_folders_with_obj,name = 't1').start()
    threading.Thread(target=app.display_activity_on_pc_recon, name = 't2').start()
    threading.Thread(target=app.add_to_log_screen, name = 't3').start()
    threading.Thread(target=app.add_to_log_screen_from_exyn_log, name = 't4').start()
    app.mainloop()
