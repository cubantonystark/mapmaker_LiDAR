'''
Mesh generation from PointClouds.
(C) 2022 - 2024, Reynel Rodriguez
All rights reserved.
For Enya, Jonathan, and Willy.

Compile with pyinstaller MM_pc2mesh.py --icon=gui_images/ARTAK_103_drk.ico --collect-all=pymeshlab --onefile --collect-all=open3d
'''

import open3d as o3d
import open3d.visualization.gui as gui
import open3d.visualization.rendering as rendering
from datetime import date, datetime
import PIL.Image
import py3dtiles
import os, platform, shutil, zipfile, logging, sys, glob, utm, time, pymeshlab, psutil, threading, copy
from tkinter import *
from tkinter import ttk
from tkinter import filedialog, messagebox

PIL.Image.MAX_IMAGE_PIXELS = None

level = logging.INFO
format = '%(message)s'
handlers = [logging.StreamHandler()]
logging.basicConfig(level=level, format='%(asctime)s \033[1;34;40m%(levelname)-8s \033[1;37;40m%(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S', handlers=handlers)

o3d.utility.set_verbosity_level(o3d.utility.VerbosityLevel.Error)

class pc2mesh():
    
    def load_pts(self, fullpath):
        
        message = 'INFO Converting PointCloud. File: ' + str(fullpath)
        logging.info('Converting PointCloud. File: ' + str(fullpath))
        self.write_to_log(path, separator, message)                
        
        pcd = o3d.io.read_point_cloud(fullpath)

        fullpath = fullpath.replace("pts", "ply")  
        
        o3d.io.write_point_cloud(fullpath,
                                 pcd)

        return fullpath    
    
    def load_e57(self, fullpath):
        
        message = 'INFO Converting PointCloud. File: ' + str(fullpath)
        logging.info('Converting PointCloud. File: ' + str(fullpath))
        self.write_to_log(path, separator, message)                
        
        ms = pymeshlab.MeshSet()
        ms.load_new_mesh(fullpath)
        fullpath = fullpath.replace("e57", "ply")  
        
        ms.save_current_mesh(fullpath,
                             save_vertex_color=True,
                             save_vertex_coord=True,
                             save_vertex_normal=True,
                             save_face_color=True,
                             save_wedge_texcoord=True,
                             save_wedge_normal=True)

        return fullpath

    def process_ply_as_tiles(self, with_texture_output_folder, fullpath, post_dest_folder, model_dest_folder):  
        
        path, filename = os.path.split(fullpath)

        path, filename = os.path.split(fullpath)
    
        file, ext = os.path.splitext(filename)
        
        file = file.replace('.', '_')
        
        fullpath = path+separator+file+ext
        
        fullpath = os.path.join(os.getcwd(), fullpath.replace('.ex', '.ply').replace('ARTAK_MM/DATA/Scanner_Logs/', ''))
            
        message = 'INFO Loading PointCloud. File: ' + str(fullpath)
        logging.info('Loading PointCloud. File: ' + str(fullpath))
        self.write_to_log(path, separator, message)        
        
        temp_folder = filename.replace('.ply', '').replace('.pts', '')
        
        model_filename = 'tpc_Model.ply'
        
        outfolder = with_texture_output_folder+separator+designator+temp_folder
        
        ms = pymeshlab.MeshSet()
        ms.load_new_mesh(fullpath)
        
        logging.info('Creating Tiles.')    
        message = 'INFO Creating Tiles.'
        self.write_to_log(path, separator, message)          
        
        try:
            
            cmd = "py3dtiles convert " + fullpath + " --out " + outfolder + " --srs_in 4979 -v > "+log_folder + separator + "runtime.log"   
      
            os.system(cmd)
            
        except ValueError:
            
            message = 'ERROR This PointCloud cannot be tiled. Aborting.'
            logging.error('This PointCloud cannot be tiled. Aborting.')
            self.write_to_log(path, separator, message)            
        
        logging.info('Compressing.')    
        message = 'INFO Compressing.'
        self.write_to_log(path, separator, message)
        
        shutil.make_archive(post_dest_folder + separator + designator + temp_folder, 'zip', outfolder)
        
        # Since this PC is too heavy to be displayed by O3d, we will downsample it to make it ligter and display better
        
        pcd = o3d.io.read_point_cloud(fullpath)
        
        vox_size = 0.05
            
        downpcd = pcd.voxel_down_sample(voxel_size = vox_size)
        
        model_destination = os.path.join(model_dest_folder, model_filename)
        
        o3d.io.write_point_cloud(model_destination, 
                                    downpcd, 
                                    format='auto', 
                                    write_ascii=False, 
                                    compressed=False, 
                                    print_progress=False)
        
        shutil.rmtree("ARTAK_MM/DATA/Processing/" + folder_type + separator + pc_folder)
        
        if os.path.exists("coords.txt"):
            
            os.remove("coords.txt")
            
        if os.path.exists("exlogs.txt"):
            
            os.remove("exlogs.txt")        
            
        try:
            
            os.unlink(dest_after_xcloud)
            
        except NameError:
            
            pass
        
        # Remove the status flag for MM_GUI progressbar
        with open(log_folder + "status.log", "w") as status:
            status.write("done")
            
        if "True" in auto_open:
            
            self.open_obj_model(model_dest_folder)
            
        message = 'INFO Processing Complete.\n'
        logging.info('Processing Complete.')
        self.write_to_log(path, separator, message)
        messagebox.showinfo('ARTAK 3D Map Maker', 'Tiling Process Complete.')
        
        current_system_pid = os.getpid()
    
        ThisSystem = psutil.Process(current_system_pid)
        ThisSystem.terminate()          
        
        sys.exit()    
    
    def process_exlog(self, exlog_path):
        
        global dest_after_xcloud
        
        exlog_file, exlog_file_extension = os.path.splitext(exlog_path)
        
        exlog_filepath, exlog_file_name = os.path.split(exlog_file)
        
        exlog_filename_converted = exlog_file_name+exlog_file_extension
        
        dest = "\\\wsl.localhost/Ubuntu-22.04\\home\\mapmaker\\exyn\\exlogs\\"+exlog_filename_converted
        
        gen_file_excloud = exlog_file_name+".prc.id.cc.nrm.rgb.ply"
        
        xcloud_file_copied = exlog_file_name+".ply"
        
        origin_after_xcloud = "\\\wsl.localhost/Ubuntu-22.04\\home\\mapmaker\\exyn\\exlogs\\"+gen_file_excloud
        
        dest_after_xcloud = os.path.join(os.getcwd(), 'ARTAK_MM/DATA/Generated_PointClouds/'+xcloud_file_copied)
        
        logging.info('Extracting PointCloud.')    
        message = 'INFO Extracting PointCloud.'
        self.write_to_log(path, separator, message)         

        shutil.copy(exlog_path, dest)

        cmd = 'wsl --user mapmaker -e bash -c "export LOGFILE='+exlog_filename_converted+' && /snap/bin/docker load < /home/mapmaker/exyn/excloud/exynai-runtime-bionic_23.10.0_base.tar && /snap/bin/docker run -it --mount type=bind,source=/home/mapmaker/exyn/exlogs,target=/home/exlogs exynai-runtime-bionic:23.10.0_base excloud -i /home/exlogs/$LOGFILE --colors --keep_uncolorized --d-cloud_remove_nonstatic_params-trajectory_params-max_dataset_duration 3600 -w /home/exlogs | tee /home/mapmaker/exyn/runtime.log && exit; exec bash"'
        os.system(cmd)
        
        with open("\\\wsl.localhost/Ubuntu-22.04\\home\\mapmaker\\exyn\\runtime.log", "r") as log_file:
            
            logs = log_file.read()
            
            if 'This logfile is not indexed, please use --reindex to fix it' in logs:
                
                logging.info('Exlog '+exlog_filename_converted+' is not indexed. Attempting reindexing.')   
                message = 'INFO Exlog '+exlog_filename_converted+' is not indexed. Attempting reindexing.'
                self.write_to_log(path, separator, message)
                
                cmd = 'wsl --user mapmaker -e bash -c "export LOGFILE='+exlog_filename_converted+' && /snap/bin/docker run -it --mount type=bind,source=/home/mapmaker/exyn/exlogs,target=/home/exlogs exynai-runtime-bionic:23.10.0_base exlog --reindex /home/exlogs/$LOGFILE --force | tee /home/mapmaker/exyn/runtime.log && exit; exec bash"'
                os.system(cmd)
                
                exlog_filename_reindexed = exlog_file_name+'.reindex'+exlog_file_extension
                
                cmd = 'wsl --user mapmaker -e bash -c "export LOGFILE='+exlog_filename_reindexed+' && /snap/bin/docker load < /home/mapmaker/exyn/excloud/exynai-runtime-bionic_23.10.0_base.tar && /snap/bin/docker run -it --mount type=bind,source=/home/mapmaker/exyn/exlogs,target=/home/exlogs exynai-runtime-bionic:23.10.0_base excloud -i /home/exlogs/$LOGFILE --colors --keep_uncolorized --d-cloud_remove_nonstatic_params-trajectory_params-max_dataset_duration 3600 -w /home/exlogs | tee /home/mapmaker/exyn/runtime.log && exit; exec bash"'
                os.system(cmd)   
                
                with open("\\\wsl.localhost/Ubuntu-22.04\\home\\mapmaker\\exyn\\runtime.log", "r") as log_file:
                    
                    logs = log_file.read()
                    
                    if 'Exyn::Exception thrown at' in logs:
                                
                        with open(log_folder + "status.log", "w") as status:
                            status.write("error")            
                        
                        # Announce error and terminate.
                        messagebox.showerror('ARTAK 3D Map Maker', 'Corrupted Exlog. Unable to process. Aborting.')
                        
                        sys.exit()
                        
                gen_file_exloud = exlog_file_name+".reindex.prc.id.cc.nrm.rgb.ply"
                
                origin_after_xcloud = "\\\wsl.localhost/Ubuntu-22.04\\home\\mapmaker\\exyn\\exlogs\\"+gen_file_excloud
                
                xcloud_file_copied = exlog_file_name+".reindex.prc.id.cc.nrm.rgb.ply"
                
                dest_after_xcloud = os.path.join(os.getcwd(), "ARTAK/_MM/DATA/Generated_PointClouds/"+xcloud_file_copied)
                
            elif 'Chunk alignment fault; guard word was wrong' in logs:
                
                with open(log_folder + "status.log", "w") as status:
                    status.write("error")            
                
                # Announce error and terminate.
                messagebox.showerror('ARTAK 3D Map Maker', 'Chunk alignment error. Unable to process exlog. Aborting.')
                
                sys.exit()     
                
            elif 'Exyn::Exception thrown at' in logs:
                
                with open(log_folder + "status.log", "w") as status:
                    status.write("error")            
                
                # Announce error and terminate.
                messagebox.showerror('ARTAK 3D Map Maker', 'Corrupted Exlog. Unable to process. Aborting.')
                
                sys.exit()

        shutil.copy(origin_after_xcloud, dest_after_xcloud)
        
        cmd = 'wsl --user mapmaker -e bash -c "sudo rm -rf /home/mapmaker/exyn/exlogs/* && exit; exec bash"'
        os.system(cmd)

        fullpath = dest_after_xcloud
    
        logging.info('PointCloud Extracted.')   
        message = 'INFO PointCloud Extracted.'
        self.write_to_log(path, separator, message)
        
        if 'tpc_' in designator:
            
            self.process_ply_as_tiles(with_texture_output_folder, fullpath, post_dest_folder, model_dest_folder)
        
        else:
            
            return fullpath    
    
    def get_file(self):
        
        global file_ext_check, file_origin, zip_file_for_compression, raw_obj, server_addr, resulting_mesh_type, auto_open, swap_axis, path, filename, mesh_output_folder, gen_path_folder, simplified_output_folder, with_texture_output_folder, obj_file, separator, c, log_name, lat, lon, elev, utm_easting, utm_northing, zone, log_name, log_folder, pc_folder, post_dest_folder, model_dest_folder, face_number, designator, folder_type, folder_suffix, texture_size
        
        root = Tk()
        root.iconbitmap(default='gui_images/ARTAK_103_drk.ico')
        root.after(1, lambda: root.focus_force())
        root.withdraw()
        
        with open("settings.cfg", "r") as settings:
            cfg = settings.readlines()
            
        raw_obj, server_addr, resulting_mesh_type, auto_open, upload_yn, del_after_xfer = cfg
        
        raw_obj = raw_obj.rstrip()
        server_addr = server_addr.rstrip()
        resulting_mesh_type = resulting_mesh_type.rstrip()
        auto_open = auto_open.rstrip()
        upload_yn = upload_yn.rstrip()
        del_after_xfer = del_after_xfer.rstrip()
        
        with open("coords.txt", "r") as coords:
            
            coordinates = coords.read()
            
        lat, lon, elev = coordinates.split(",")
        
        lat = lat.strip()
        lon = lon.strip()
        elev = elev.strip()
        
        with open("ARTAK_MM/LOGS/runtime.log", "r") as runtime:
            fullpath = runtime.read().strip()
            
        if 'None' in fullpath:
            
            current_system_pid = os.getpid()
            ThisSystem = psutil.Process(current_system_pid)
            ThisSystem.terminate() 
            
        with open("ARTAK_MM/LOGS/status.log", "w") as status:
            status.write("running") 
            
        if resulting_mesh_type == "m":
            
            mesh_depth = 13
            face_number = 500000
            designator = 'm_'
            folder_type = 'b1'
            folder_suffix = '_m'
            texture_size = 8192 
            
        elif resulting_mesh_type == "tm":
            
            mesh_depth = 13
            face_number = 4500000
            designator = 'tm_'
            folder_type = 'b2'
            folder_suffix = '_tm'
            texture_size = 16384         
            
        elif resulting_mesh_type == "tpc":
            
            designator = 'tpc_'
            folder_type = 'b2a'
            folder_suffix = '_tpc'   

        else:
            
            mesh_depth = 13
            face_number = 500000
            designator = 'm_'
            folder_type = 'b1'
            folder_suffix = '_m'
            texture_size = 8192  
        
        today = date.today()
        now = datetime.now()
        d = today.strftime("%d%m%Y")
        ct = now.strftime("%H%M%S")   

        if platform.system == 'Windows':
            separator = '\\'
            
        else:
            
            separator = '/'  
            
        # Define o3d data object to handle PointCloud
        ply_point_cloud = o3d.data.PLYPointCloud()

        # We will encode the lat and lon into utm compliant coordinates for the xyz file and retrieve the utm zone for the prj file

        utm_easting, utm_northing, zone, zone_letter = utm.from_latlon(float(lat), float(lon))
        utm_easting = "%.2f" % utm_easting
        utm_northing = "%.2f" % utm_northing

        # Separate source path from filename
        path, filename = os.path.split(fullpath)
        path = path.replace("<_io.TextIOWrapper name='", '')
        filename = filename.replace("' mode='r' encoding='cp1252'>", '')
        
        filename1 = os.path.join(path, filename)

        file_name, extension = os.path.splitext(filename)
        
        file_name = file_name.replace(".", '_')
        
        filename = file_name+extension        

        fullpath = path + separator + filename
        
        if os.path.exists(filename1):
            
            os.rename(filename1, fullpath)

        if 'None' in fullpath:
            sys.exit()
            
        path, filename = os.path.split(fullpath)
        
        logfilename = designator + filename.replace('.ply', '').replace('.pts', '').replace('.obj', '').replace('.e57', '').replace('.ex', '')
        pc_folder = logfilename
        
        log_name = designator + filename.replace('.ply', '').replace('.pts', '').replace('.obj', '').replace('.e57', '').replace('.ex', '') + "_" + str(d) + "_" + str(ct) + ".log"

        # Derive destination folders from source path
        post_dest_folder = "ARTAK_MM/POST/Lidar" + separator + pc_folder.replace("m_m_", "m_").replace("tm_tm_", "tm_") + separator + "Data"
        model_dest_folder = "ARTAK_MM/POST/Lidar" + separator + pc_folder.replace("m_m_", "m_").replace("tm_tm_", "tm_") + separator + "Data/Model"
        mesh_output_folder = "ARTAK_MM/DATA/Processing/"+folder_type + separator + pc_folder.replace("m_m_", "m_").replace("tm_tm_", "tm_") + separator + "mesh"+folder_suffix
        simplified_output_folder = "ARTAK_MM/DATA/Processing/"+folder_type + separator + pc_folder.replace("m_m_", "m_").replace("tm_tm_", "tm_") + separator + "simplified"+folder_suffix
        gen_path_folder = "ARTAK_MM/DATA/Generated_Mesh"
        with_texture_output_folder = "ARTAK_MM/DATA/Processing/"+folder_type + separator + pc_folder.replace("m_m_", "m_").replace("tm_tm_", "tm_") + separator + "final"+folder_suffix
        log_folder = "ARTAK_MM/LOGS/"
        zip_file_for_compression = designator + filename.replace(".ex", ".zip").replace(".obj", ".zip").replace(".ply", ".zip").replace(".pts", ".zip")
        
        # Create directories within the source folder if they dont exist
        if not os.path.exists(mesh_output_folder):
            os.makedirs(mesh_output_folder)
        if not os.path.exists(simplified_output_folder):
            os.makedirs(simplified_output_folder, mode=777)
        if not os.path.exists(with_texture_output_folder):
            os.makedirs(with_texture_output_folder, mode=777)
        if not os.path.exists(post_dest_folder):
            os.makedirs(post_dest_folder, mode=777)
        if not os.path.exists(model_dest_folder):
            os.makedirs(model_dest_folder, mode=777)
                
        if '.e57' in fullpath:
            
            fullpath = self.load_e57(fullpath)     
            
        if '.pts' in fullpath:
            
            fullpath = self.load_pts(fullpath)         
            
        if '.ex' in fullpath:
            
            fullpath = self.process_exlog(fullpath)       
            
        if 'tpc_' in designator:
            
            self.process_ply_as_tiles(with_texture_output_folder, fullpath, post_dest_folder, model_dest_folder)         

        if "m_" in designator:
            # Create xyz and prj based on lat and lon provided
            prj_1 = 'PROJCS["WGS 84 / UTM zone '
            prj_2 = '",GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]],PROJECTION["Transverse_Mercator"],PARAMETER["latitude_of_origin",0],PARAMETER["central_meridian",-81],PARAMETER["scale_factor",0.9996],PARAMETER["false_easting",500000],PARAMETER["false_northing",0],UNIT["metre",1,AUTHORITY["EPSG","9001"]],AXIS["Easting",EAST],AXIS["Northing",NORTH],AUTHORITY["EPSG","32617"]]'

            with open(with_texture_output_folder + separator + logfilename + '.xyz', 'w') as xyz:
                xyz.write(str(utm_easting + " " + str(utm_northing) + " " + "101.000"))

            with open(with_texture_output_folder + separator + logfilename + '.prj', 'w') as prj:
                prj.write(str(prj_1) + str(zone) + str(prj_2))
              
        if ".obj" in filename:

            origin = 'obj'
            
            message = 'INFO Loading OBJ. File: '+str(fullpath)
            logging.info('Loading OBJ. File: '+str(fullpath))
            file_origin = fullpath
            self.write_to_log(path, separator, message)
            shutil.copy(fullpath, simplified_output_folder)
            shutil.rmtree(mesh_output_folder)
            generated_mesh = fullpath
            self.mesh_processing(generated_mesh, texture_size, origin)   
            
        if 'True' in raw_obj:
            
            message = 'INFO Standalone Mesh requested.'
            logging.info('Standalone Mesh requested.')
            self.write_to_log(path, separator, message)     
        
        message = 'INFO Loading PointCloud. File: ' + str(fullpath)
        logging.info('Loading PointCloud. File: ' + str(fullpath))
        self.write_to_log(path, separator, message)
        file_ext_check = fullpath
        #message = 'INFO Processing to depth: ' + str(mesh_depth)
        #logging.info('Processing to depth: ' + str(mesh_depth))
        #self.write_to_log(path, separator, message) 
        
        pcd = o3d.io.read_point_cloud(fullpath)
        
        self.downsample(pcd, texture_size, mesh_depth)     
    
    def downsample(self, pcd, texture_size, mesh_depth):
        # We need to downsample the PointCloud to make it less dense and easier to work with
        message = "INFO "+str(pcd)
        logging.info(str(pcd))
        self.write_to_log(path, separator, message)        
        message = "INFO Downsampling."
        logging.info("Downsampling.")
        self.write_to_log(path, separator, message)
        
        vox_size = 0.02
            
        downpcd = pcd.voxel_down_sample(voxel_size = vox_size)

        logging.info(str(downpcd)+"\r")
        message = "INFO "+str(downpcd)
        self.write_to_log(path, separator, message)
        self.compute_normals_and_generate_mesh(downpcd, mesh_depth, texture_size)  
    def compute_normals_and_generate_mesh(self, downpcd, mesh_depth, texture_size):

        # Since some PointClouds don't include normals information (needed for texture and color extraction) we will have to calculate it.
        message = 'INFO Computing Normals.'
        logging.info('Computing Normals.')
        self.write_to_log(path, separator, message)
        downpcd.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=30))

        logging.info('Generating Mesh.')
        message = 'INFO Generating Mesh.'
        self.write_to_log(path, separator, message)

        mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(downpcd, depth=mesh_depth, width=0, scale=1.1,
                                                                         linear_fit=False)[0]
        generated_mesh = mesh_output_folder + separator + designator + filename.replace('.ply', '.obj').replace('.pts', '.obj').replace('.ex', '.obj').replace('.e57', '.obj')

        message = 'INFO Exporting Mesh.'
        logging.info('Exporting Mesh.')
        self.write_to_log(path, separator, message)
        
        o3d.io.write_triangle_mesh(generated_mesh,
                                   mesh,
                                   write_ascii=False,
                                   compressed=True,
                                   write_vertex_normals=True,
                                   write_vertex_colors=True,
                                   write_triangle_uvs=True,
                                   print_progress=False)

        mesh_file_size = int(os.path.getsize(generated_mesh))
        
        if mesh_file_size > 20000000000:
            
            mesh_depth = 12
            origin = 'pc'
            message = 'WARNING Mesh is not memory friedly. Retrying with safer parameters.'
            logging.warning('Mesh is not memory friedly. Retrying with safer parameters.')
            self.write_to_log(path, separator, message)
            self.compute_normals_and_generate_mesh(downpcd, mesh_depth, texture_size)

        else:
            origin = 'pc'
            self.mesh_processing(generated_mesh, texture_size, origin)

    def mesh_processing(self, generated_mesh, texture_size, origin):

        try:
            
            # We will use Meshlab from now on to to handle the processing.
            ms = pymeshlab.MeshSet()
            message = 'INFO Analyzing.'
            logging.info('Analyzing.')
            self.write_to_log(path, separator, message)
            ms.load_new_mesh(generated_mesh)
            
            if 'obj' in origin:
                
                newpath = generated_mesh
                message = 'INFO Bypassing Mesh Refinement.'
                logging.info('Bypassing Mesh Refinement.')
                self.write_to_log(path, separator, message)                
                
                pass
            
            else:

                try:
                    
                    # In order to get closer to the usable faces as much as possible, we will calculate the unusable face edge legth by dividing the
                    # mesh diagonal bounding box mesurement by 200. This is the value that meshlab uses as a default on its filter.
                    # Caveat: If the object was edited too much (The total manually removed faces is higher than 25% of the entire bounding box), the bounding box method to determine
                    # the face length will bee too much, therefore, we will have to use an arbitrary static value; we have found that 1.6 works well.
    
                    boundingbox = ms.current_mesh().bounding_box()
                    diag = boundingbox.diagonal()
    
                    t_hold = diag / 200
    
                    p = pymeshlab.PercentageValue(2)
                    message = 'INFO Refining.'
                    logging.info('Refining.')
                    self.write_to_log(path, separator, message)
                    # We will select faces that are long based on the bounding box calculation and then remove them
                    ms.apply_filter('compute_selection_by_edge_length',
                                    threshold=t_hold)
                    ms.apply_filter('meshing_remove_selected_faces')
                    # The selection process and removal of long faces will create floaters, we will remove isolated faces
                    ms.apply_filter('meshing_remove_connected_component_by_diameter',
                                    mincomponentdiag = p)
                    # if this is a generated file from exyn sensors, then we need to use 'safe' values different from the leica ones.
                    
                    file_ext_check_filename, file_ext_check_extension = os.path.splitext(file_ext_check)
    
                    if ".ply" in file_ext_check_extension or ".ex" in file_ext_check_extension:
                        
                        t_hold = 0.12

                    elif ".pts" in file_ext_check_extension or ".e57" in file_ext_check_extension:
                        
                        t_hold = 0.09            

                    else:
                        
                        t_hold = 3
    
                    # Since there will still be some long faces, we will mark them and remove them, this time applying a 0.06 thershold. This is
                    ms.apply_filter('compute_selection_by_edge_length',threshold=t_hold)
                    ms.apply_filter('meshing_remove_selected_faces')
                    # Then we remove any isolated faces (floaters) that might still be laying around
                    ms.apply_filter('meshing_remove_connected_component_by_diameter',
                                    mincomponentdiag=p)
                    message = 'INFO Exporting Mesh.'
                    logging.info('Exporting Mesh.')
                    self.write_to_log(path, separator, message)
    
                    newpath = simplified_output_folder + separator + designator + filename.replace('.ply', '.obj').replace('.pts', '.obj').replace('.ex', '.obj').replace('.e57', '.obj')
                    newpath_gen = gen_path_folder + separator + filename.replace('.ply', '.obj').replace('.pts', '.obj').replace('.ex', '.obj').replace('.e57', '.obj')
                    
                    ms.save_current_mesh(newpath,
                                         save_vertex_color=True,
                                         save_vertex_coord=True,
                                         save_vertex_normal=True,
                                         save_face_color=True,
                                         save_wedge_texcoord=True,
                                         save_wedge_normal=True,
                                         save_polygonal=True)
                    
                    shutil.copyfile(newpath, newpath_gen)

                    if 'True' in raw_obj:
                        
                        try:
                            shutil.rmtree("ARTAK_MM/DATA/Processing/" + folder_type + separator + pc_folder)
                            
                        except FileNotFoundError:
                            pass                        
                        
                        # Remove the status flag for MM_GUI progressbar
  
                        with open(log_folder + "status.log", "w") as status:
                            status.write("done")                      
                        
                        message = 'INFO Standalone Mesh Creation Complete.\n'
                        logging.info('Raw Standalone Mesh Creation Complete.')
                        self.write_to_log(path, separator, message)
                        messagebox.showinfo('ARTAK 3D Map Maker', 'Standalone Mesh Creation Complete.')
                        
                        current_system_pid = os.getpid()
                    
                        ThisSystem = psutil.Process(current_system_pid)
                        ThisSystem.terminate()                          
                        
                except pymeshlab.pmeshlab.PyMeshLabException:
    
                    try:
    
                        ms.load_new_mesh(generated_mesh)
                        logging.warning('Mesh not optimal. Retargeting parameters (1).\r')
                        message = 'WARNING Mesh not optimal. Retargeting parameters (1).'
                        self.write_to_log(path, separator, message)
    
                        boundingbox = ms.current_mesh().bounding_box()
                        diag = boundingbox.diagonal()
                        t_hold = diag / 200
    
                        p = pymeshlab.PercentageValue(2)
    
                        logging.info('Refining.')
                        message = 'INFO Refining.'
                        self.write_to_log(path, separator, message)
    
                        # We will select faces that are long based on the bounding box calculation and then remove them
                        ms.apply_filter('compute_selection_by_edge_length',
                                        threshold=t_hold)
                        ms.apply_filter('meshing_remove_selected_faces')
    
                        # The selection process and removal of long faces will create floaters, we will remove isolated faces
                        ms.apply_filter('meshing_remove_connected_component_by_diameter',
                                        mincomponentdiag=p)
    
                        if ".ply" in file_ext_check_extension or ".ex" in file_ext_check_extension:

                            t_hold = 0.25
    
                        elif ".pts" in file_ext_check_extension or ".e57" in file_ext_check_extension:
                            t_hold = 0.1
    
                        else:
                            t_hold = t_hold
    
                        # Since there will still be some long faces, we will mark them and remove them, this time applying a 0.06 thershold. This is
                        ms.apply_filter('compute_selection_by_edge_length',
                                        threshold=t_hold)
                        ms.apply_filter('meshing_remove_selected_faces')
    
                        # Then we remove any isolated faces (floaters) that might still be laying around
                        ms.apply_filter('meshing_remove_connected_component_by_diameter',
                                        mincomponentdiag = p)
    
                        message = 'INFO Exporting Mesh.'
                        
                        newpath = simplified_output_folder + separator + filename.replace('.ply', '.obj').replace('.pts', '.obj').replace('.ex', '.obj').replace('.e57', '.obj')
                        newpath_gen = gen_path_folder + separator + filename.replace('.ply', '.obj').replace('.pts', '.obj').replace('.ex', '.obj').replace('.e57', '.obj')
                        
                        ms.save_current_mesh(newpath,
                                             save_vertex_color=True,
                                             save_vertex_coord=True,
                                             save_vertex_normal=True,
                                             save_face_color=True,
                                             save_wedge_texcoord=True,
                                             save_wedge_normal=True,
                                             save_polygonal=True)
                        
                        shutil.copyfile(newpath, newpath_gen)
                        
                        if 'True' in raw_obj:
                        
                            with open(log_folder + "status.log", "w") as status:
                                status.write("done")                      
                        
                            message = 'INFO Standalone Mesh Creation Complete.\n'
                            logging.info('Raw Standalone Mesh Creation Complete.')
                            self.write_to_log(path, separator, message)
                            messagebox.showinfo('ARTAK 3D Map Maker', 'Raw Standalone Mesh Creation Complete.')
                            
                            current_system_pid = os.getpid()
                        
                            ThisSystem = psutil.Process(current_system_pid)
                            ThisSystem.terminate()                 
    
                    except pymeshlab.pmeshlab.PyMeshLabException:
    
                        try:
    
                            ms.load_new_mesh(generated_mesh)
                            logging.warning('Mesh not optimal. Retargeting parameters (2).\r')
                            message = 'WARNING Mesh not optimal. Retargeting parameters (2).'
                            self.write_to_log(path, separator, message)
                            boundingbox = ms.current_mesh().bounding_box()
                            diag = boundingbox.diagonal()
                            t_hold = diag / 200
                            p = pymeshlab.PercentageValue(2)
                            logging.info('Refining.')
                            message = 'INFO Refining'
                            self.write_to_log(path, separator, message)
                            # We will select faces that are long based on the bounding box calculation and then remove them
                            ms.apply_filter('compute_selection_by_edge_length',
                                            threshold=t_hold)
                            ms.apply_filter('meshing_remove_selected_faces')
    
                            # The selection process and removal of long faces will reate floaters, we will remove isolated faces
                            ms.apply_filter('meshing_remove_connected_component_by_diameter',
                                            mincomponentdiag=p)
    
                            t_hold = 0.5 #threshold will be the same for all if it gets this far
    
                            # Since there will still be some long faces, we will mark them and remove them, this time applying a 0.06 thershold. This is
                            ms.apply_filter('compute_selection_by_edge_length',
                                            threshold=t_hold)
                            ms.apply_filter('meshing_remove_selected_faces')
                            # Then we remove any isolated faces (floaters) that might still be laying around
                            ms.apply_filter('meshing_remove_connected_component_by_diameter',
                                            mincomponentdiag=p)
                            #logging.info("Exporting Mesh.")
                            #message = 'INFO Exporting Mesh.'
                            #self.write_to_log(path, separator, message)
    
                            newpath = simplified_output_folder + separator + filename.replace('.ply', '.obj').replace('.pts', '.obj').replace('.ex', '.obj').replace('.e57', '.obj')
                            newpath_gen = gen_path_folder + separator + filename.replace('.ply', '.obj').replace('.pts', '.obj').replace('.ex', '.obj').replace('.e57', '.obj')
                            
                            ms.save_current_mesh(newpath,
                                                 save_vertex_color=True,
                                                 save_vertex_coord=True,
                                                 save_vertex_normal=True,
                                                 save_face_color=True,
                                                 save_wedge_texcoord=True,
                                                 save_wedge_normal=True,
                                                 save_polygonal=True)
                            
                            shutil.copyfile(newpath, newpath_gen)
                            
                            if 'True' in raw_obj:
                        
                                with open(log_folder + "status.log", "w") as status:
                                    status.write("done")                      
                            
                                message = 'INFO Standalone Mesh Creation Complete.\n'
                                logging.info('Raw Standalone Mesh Creation Complete.')
                                self.write_to_log(path, separator, message)
                                messagebox.showinfo('ARTAK 3D Map Maker', 'Raw Standalone Mesh Creation Complete.')
                                
                                current_system_pid = os.getpid()
                            
                                ThisSystem = psutil.Process(current_system_pid)
                                ThisSystem.terminate()                            
    
                        except pymeshlab.pmeshlab.PyMeshLabException:
    
                            # Cleanup
                            try:
                                shutil.rmtree("ARTAK_MM/DATA/Processing/" + folder_type + separator + pc_folder)
                                os.unlink(dest_after_xcloud)
                                
                            # Remove the status flag for MM_GUI progressbar
                            
                            except (FileNotFoundError, NameError):
                                pass

                            with open(log_folder + "status.log", "w") as status:
                                status.write("error")
 
                            message = 'ERROR Could not compute Mesh from PointCloud. Aborting.'
                            logging.error('Could not compute Mesh from PointCloud. Aborting.')
                            self.write_to_log(path, separator, message)
                            
                            message = 'ERROR Process terminated.'
                            logging.error('Process terminated.')
                            self.write_to_log(path, separator, message)
      
                            # Announce error and terminate.
                            messagebox.showerror('ARTAK 3D Map Maker', 'Could not compute Mesh from PointCloud. Aborting.')
                            
                            current_system_pid = os.getpid()

                            ThisSystem = psutil.Process(current_system_pid)
                            ThisSystem.terminate()  

            m = ms.current_mesh()
            v_number = m.vertex_number()
            f_number = m.face_number()
            logging.info("Overall Target FC: "+str(face_number)+".\r")
            message = "INFO Overall Target FC: "+str(face_number)+"."
            self.write_to_log(path, separator, message)
            logging.info("Initial VC: "+str(v_number)+". Initial FC: "+str(f_number)+".\r")
            message = 'INFO Initial VC: ' + str(v_number) + '. Initial FC: ' + str(f_number) + "."
            self.write_to_log(path, separator, message)

            # Let's take a look at the mesh file to see how big it is. We are constrained to about 120Mb in this case, therefore we
            # will have to decimate if the file is bigger than that number.

            # if f_number > 6500000:  # Decimate over 6500000 faces (approx.650Mb)
            if f_number > face_number:  # Decimate over 6500000 faces (approx.950Mb)
                
                self.decimation(ms, newpath, f_number, texture_size)

            else:
                
                logging.info("End VC: "+str(v_number)+". End FC: "+str(f_number)+". Bypassing Decimation.\r")
                message = 'INFO End VC: ' + str(v_number) + '. End FC: ' + str(f_number) + ". Bypassing Decimation."
                self.write_to_log(path, separator, message)                           
                
                newpath1 = simplified_output_folder + separator + 'decimated_' + designator + filename.replace('.ply', '.obj').replace('.pts', '.obj').replace('.ex', '.obj').replace('.e57', '.obj')

                ms.save_current_mesh(newpath1,
                                     save_vertex_color=True,
                                     save_vertex_coord=True,
                                     save_vertex_normal=True,
                                     save_face_color=True,
                                     save_wedge_texcoord=True,
                                     save_wedge_normal=True,
                                     save_polygonal=True)
        
                self.add_texture_and_materials(newpath, newpath1, texture_size)

        except MemoryError:
            
            with open(log_folder + "status.log", "w") as status:
                status.write("error")
                
            logging.error('Not enough Memory to run the process. Quitting.\r')
            message = 'ERROR Not enough Memory to run the process. Quitting.'
            self.write_to_log(path, separator, message)
            current_system_pid = os.getpid()
            ThisSystem = psutil.Process(current_system_pid)
            ThisSystem.terminate()

    def decimation(self, ms, newpath, f_number, texture_size):
        # The mesh decimation works best if we take a percentage of faces at a time. We will decimate to target amount
        # of (faces / weight) and save the file, then read the file size and if necessary (over the 185Mb threshold), we will repeat
        # the decimation process again until the resulting mesh meets the file size criteria, we will do this n times (passes).
        
        m = ms.current_mesh()
        c = 1
        
        # while f_number > 6500000:
        while f_number > face_number:
            m = ms.current_mesh()
            f_number = m.face_number()
            #target_faces = int(f_number / 1.125)
            target_faces = int(f_number / 1.5)
            logging.info("Target: "+str(int(target_faces))+" F. Iter. "+str(c)+".\r")
            message = "INFO Target: " + str(int(target_faces)) + " F. Iter. " + str(c) + "."
            self.write_to_log(path, separator, message)
            ms.apply_filter('meshing_decimation_quadric_edge_collapse',
                            targetfacenum=int(target_faces), targetperc=0,
                            qualitythr=0.8,
                            optimalplacement=True,
                            preservenormal=True,
                            autoclean=True)
            f_number = m.face_number()
            v_number = m.vertex_number()
            ratio = (abs(target_faces / f_number) - 1.1) * 10  # Efficiency ratio. resulting amt faces vs target amt of faces
            logging.info("Achieved: "+str(f_number)+" F. Ratio ==> "+"%.2f" % abs(ratio)+":1.00.\r")
            message = 'INFO Achieved: ' + str(f_number) + ' F. Ratio ==> ' + '%.2f' % abs(ratio) + ':1.00.'
            self.write_to_log(path, separator, message)
            c += 1

        m = ms.current_mesh()
        f_number = m.face_number()
        v_number = m.vertex_number()

        logging.info("End VC: "+str(v_number)+". End FC: "+str(f_number)+".\r")
        message = 'INFO End VC: ' + str(v_number) + '. End FC: ' + str(f_number) + "."
        self.write_to_log(path, separator, message)

        newpath1 = simplified_output_folder + separator + 'decimated_' + designator + filename.replace('.ply', '.obj').replace('.pts','.obj').replace('.ex','.obj').replace('.e57', '.obj')

        ms.save_current_mesh(newpath1,
                             save_vertex_color=True,
                             save_vertex_coord=True,
                             save_vertex_normal=True,
                             save_face_color=True,
                             save_wedge_texcoord=True,
                             save_wedge_normal=True,
                             save_polygonal=True)
        
        self.add_texture_and_materials(newpath, newpath1, texture_size)
        
    def add_texture_and_materials(self, newpath, newpath1, texture_size):

        # This part creates the materials and texture file (.mtl and .png) by getting the texture coordinates from the vertex,
        # tranfering the vertex info to wedges and reating a trivialized texture coordinate from the per wedge info. In the end,
        # we will just extract the texture form the color present at that texture coordinate and thats how we get the texture info into a png

        ms = pymeshlab.MeshSet()

        message = 'INFO Generating Texture and Materials.'
        logging.info('Generating Texture and Materials.')
        self.write_to_log(path, separator, message)

        ms.load_new_mesh(newpath)
        ms.load_new_mesh(newpath1)       
        
        try:
            
            itb = 3 # If itb overrun then texture needs to be bigger
                
            m_method = 'Basic'
        
            ms.apply_filter('compute_texcoord_parametrization_triangle_trivial_per_wedge',
                            sidedim = 0,
                            textdim = texture_size,
                            border = itb,
                            method = m_method)
            
        except pymeshlab.pmeshlab.PyMeshLabException:
            
            # Announce error and terminate.
            
            with open(log_folder + "status.log", "w") as status:
                status.write("error")            
                
            logging.error('ITB overrun. Quitting.')
            message = 'ERROR ITB overrun. Quitting.'
            self.write_to_log(path, separator, message)
            messagebox.showerror('ARTAK 3D Map Maker', 'Could not compute Mesh from PointCloud. Aborting.')
            current_system_pid = os.getpid()
            ThisSystem = psutil.Process(current_system_pid)
            ThisSystem.terminate()         
            
        percentage = pymeshlab.PercentageValue(2)

        newpath_texturized = with_texture_output_folder + separator + designator + filename.replace('.ply', '.obj').replace('.pts','.obj').replace('.ex','.obj').replace('decimated_', '').replace('.e57', '.obj')

        model_path = model_dest_folder + separator + designator + 'Model.obj'

        #Here we transfer the texture
     
        ms.apply_filter('transfer_attributes_to_texture_per_vertex',
                         sourcemesh = 0,
                         targetmesh  = 1,
                         attributeenum = 0,
                         upperbound = percentage,
                         textname = designator + 'texture.png',
                         textw = texture_size,
                         texth = texture_size,
                         overwrite = False,
                         pullpush = True)

        ms.save_current_mesh(newpath_texturized,
                             save_vertex_color=False,
                             save_vertex_coord=False,
                             save_vertex_normal=False,
                             save_face_color=True,
                             save_wedge_texcoord=True,
                             save_wedge_normal=True)

        ms.save_current_mesh(model_path,
                             save_vertex_color=False,
                             save_vertex_coord=False,
                             save_vertex_normal=False,
                             save_face_color=True,
                             save_wedge_texcoord=True,
                             save_wedge_normal=True)

        # We need check if we have to compress the texture file
        
        print("\n")    
        logging.info('Compressing texture.')   
        message = 'INFO Compressing texture.'
        self.write_to_log(path, separator, message)       

        img = PIL.Image.open(with_texture_output_folder + separator + designator + 'texture.png')
        img = img.convert("P", palette=PIL.Image.WEB, colors = 256)
        
        img.save(with_texture_output_folder + separator + designator  + 'texture.png', optimize=True)
        img.save(model_dest_folder + separator +  designator  + 'texture.png', optimize=True)

        # Let's compress
        
        zip_file = with_texture_output_folder + separator + designator + filename.replace('.obj', '').replace('.ply','').replace('.pts', '').replace('.ex', '').replace('.e57', '') + '.zip'        
        
        if 'v1' in resulting_mesh_type:
            
            logging.info('Compressing to '+with_texture_output_folder + '/'+ str(zip_file_for_compression)) 
            message = 'INFO Compressing to '+with_texture_output_folder +'/'+ str(zip_file_for_compression)
            self.write_to_log(path, separator, message)
        
        self.compress_into_zip(with_texture_output_folder, newpath, zip_file)
        
        files = [f for f in glob.glob(with_texture_output_folder + "/*.zip")]
        
        for file in files:
            shutil.copy(file, post_dest_folder)

        # Cleanup finish

        try:
            os.system('@taskkill /im Obj2Tiles.exe /F >nul 2>&1')
            shutil.rmtree("ARTAK_MM/DATA/Processing/" + folder_type + separator + pc_folder)
            os.remove("coords.txt")
            os.remove("exlogs.txt")
            
        except (FileNotFoundError, NameError):
            pass
        
        # Remove the status flag for MM_GUI progressbar
        with open(log_folder + "status.log", "w") as status:
            status.write("done")
            
        if "True" in auto_open:
            
            self.open_obj_model(model_dest_folder)
            
        message = 'INFO Reconstruction Complete.\n'
        logging.info('Reconstruction Complete.')
        self.write_to_log(path, separator, message)
        messagebox.showinfo('ARTAK 3D Map Maker', 'Reconstruction Complete.')
        
        current_system_pid = os.getpid()
    
        ThisSystem = psutil.Process(current_system_pid)
        ThisSystem.terminate()        

    def compress_into_zip(self, with_texture_output_folder, newpath, zip_file):
        
        if resulting_mesh_type == "tm":
            
            logging.info('Generating Tiles.')   
            message = 'INFO Generating Tiles.'
            self.write_to_log(path, separator, message)                
            
            target_to_tile = with_texture_output_folder + separator + designator + filename.replace('.ply', '.obj').replace('.pts','.obj').replace('.ex','.obj').replace('.e57', '.obj')
            
            tiles_folder = target_to_tile.replace('.obj', '')+"_tiles"
            
            os.makedirs(tiles_folder, exist_ok = True)
            
            cmd = "Obj2Tiles --lods 1 --divisions 1 --lat "+str(lat)+" --lon "+str(lon)+" --alt "+str(elev)+" "+target_to_tile+" "+tiles_folder+" --keeptextures > "+log_folder + "runtime.log"
            
            os.system(cmd) 
            
            logging.info('Done Generating Tiles.')   
            message = 'INFO Done Generating Tiles.'
            self.write_to_log(path, separator, message)   
            
            logging.info('Compressing to '+tiles_folder+separator+designator+filename.replace('.ply', '.zip').replace('.pts','.zip').replace('.ex','.zip').replace('.obj','.zip').replace('.e57', '.zip')+".")   
            message = 'INFO Compressing to '+tiles_folder+separator+designator+filename.replace('.ply', '.zip').replace('.pts','.zip').replace('.ex','.zip').replace('.obj','.zip').replace('.e57', '.zip')+"."
            self.write_to_log(path, separator, message)            
            
            shutil.make_archive(tiles_folder.replace('_tiles', ''), 'zip', tiles_folder)
            
            print("shutil.make_archive("+tiles_folder.replace('_tiles', '')+',"zip",'+tiles_folder+")")

            return
        
        if resulting_mesh_type == "m":
            
            extensions = ['.obj', '.obj.mtl', '.xyz', '.prj', '.png']        

            compression = zipfile.ZIP_DEFLATED
            
            with zipfile.ZipFile(zip_file, mode="w") as zf:
                for ext in extensions:
                    
                    try:
                        zf.write(with_texture_output_folder + separator + designator + filename.replace('.obj', '').replace('.ply','').replace('.pts', '').replace('.ex', '').replace('.e57', '') + ext, designator + filename.replace('.obj', '').replace('.ply', '').replace('.pts', '').replace('.ex', '').replace('.e57', '') + ext,
                                 compress_type = compression, compresslevel = 9)
                    except FileExistsError:
                        pass
                    except FileNotFoundError:
                        pass
                    
                zf.write(with_texture_output_folder + separator + designator + 'texture.png', designator + 'texture.png', compress_type = compression, compresslevel = 9)
    
            return    
        
    def open_obj_model(self, model_dest_folder):
        
        if 'tpc_' in model_dest_folder:
            
            model_name = 'tpc_Model.ply'
            path = os.path.join(model_dest_folder, model_name)
            
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
        
        else:
            
            if resulting_mesh_type == "m":
        
                model_name = os.path.join(model_dest_folder, "m_Model.obj")
                albedo_name = os.path.join(model_dest_folder, "m_texture.png")
                
            else:
                
                model_name = os.path.join(model_dest_folder, "tm_Model.obj")
                albedo_name = os.path.join(model_dest_folder, "tm_texture.png")
                
            model = o3d.io.read_triangle_mesh(model_name)
            material = o3d.visualization.rendering.MaterialRecord()
            material.shader = "defaultLit"        
            
            material.albedo_img = o3d.io.read_image(albedo_name)
            
            o3d.visualization.draw([{"name": "Model", "geometry": model, "material": material}], title = "ARTAK 3D Map Maker || LiDAR Edition", bg_color = [0,0,0,0], show_skybox = False, actions = None, width = 1280, height = 900)
            
            return    

    def write_to_log(self, path, separator, message):

        with open(log_folder + log_name, "a+") as log_file:
            log_file.write(str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))+" "+message + "\r")
            
        with open(log_folder + "runtime.log", "w") as log_file:
            log_file.write(str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))+" "+message + "\r")        
        time.sleep(0.5)
        return
    
if __name__ == '__main__':
    pc2mesh().get_file()