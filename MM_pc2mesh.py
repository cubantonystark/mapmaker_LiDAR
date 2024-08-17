'''
Mesh generation from PointClouds.
(C) 2022 - 2024, Reynel Rodriguez
All rights reserved.

Compile with pyinstaller MM_pc2mesh.py --icon=gui_images/ARTAK_103_drk.ico --collect-all=pymeshlab --onefile --collect-all=open3d
'''

import open3d as o3d
import open3d.visualization.gui as gui
import open3d.visualization.rendering as rendering
from datetime import date, datetime
from PIL import Image
import os, platform, shutil, zipfile, logging, sys, glob, utm, time, pymeshlab
from tkinter import Tk
from tkinter import filedialog, messagebox

Image.MAX_IMAGE_PIXELS = None

'''
level_info = logging.INFO
handlers = [logging.StreamHandler()]
logging.basicConfig(level=level_info, format='%(asctime)s \033[1;34;40m%(levelname)-8s \033[1;37;40m%(message)s',
                    datefmt='%H:%M:%S', handlers=handlers)
'''

class CustomFormatter(logging.Formatter):

    grey = "\x1b[38;20m"
    blue = "\x1b[34;40m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    time_msg = "%(asctime)s "
    format = "%(levelname)s "
    message = "%(message)s"
    
    FORMATS = {
        logging.DEBUG: time_msg + grey + format + reset + message,
        logging.INFO: time_msg + blue + format + reset + message,
        logging.WARNING: time_msg + yellow + format + reset + message,
        logging.ERROR: time_msg + red + format + reset + message,
        logging.CRITICAL: time_msg + bold_red + format + reset + message
        }
    
    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)
    
# create logger with 'spam_application'
log = logging.getLogger("MM_pc2mesh.py")
log.setLevel(logging.DEBUG)

# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

ch.setFormatter(CustomFormatter())

log.addHandler(ch)

o3d.utility.set_verbosity_level(o3d.utility.VerbosityLevel.Error)

mesh_depth = 11

class meshing():

    def load_e57(self, e57path):

        mesh_depth = 11
        ms = pymeshlab.MeshSet()
        ms.load_new_mesh(e57path)
        fullpath = e57path.replace("e57", "ply")  
        
        ms.save_current_mesh(fullpath,
                             save_vertex_color=True,
                             save_vertex_coord=True,
                             save_vertex_normal=True,
                             save_face_color=True,
                             save_wedge_texcoord=True,
                             save_wedge_normal=True)

        return fullpath, mesh_depth

    def get_PointCloud(self):
        
        global server_addr, resulting_mesh_type, auto_open, swap_axis, path, filename, mesh_output_folder, gen_path_folder, simplified_output_folder, with_texture_output_folder, obj_file, separator, c, log_name, lat, lon, utm_easting, utm_northing, zone, log_name, log_folder, pc_folder, post_dest_folder, model_dest_folder, face_number, designator, folder_type, folder_suffix, texture_size

        with open("settings.cfg", "r") as settings:
            cfg = settings.readlines()
            
        server_addr, resulting_mesh_type, auto_open, upload_yn, del_after_xfer = cfg
        
        root = Tk()
        root.iconbitmap(default='gui_images/ARTAK_103_drk.ico')
        root.after(1, lambda: root.focus_force())
        root.withdraw()

        fullpath = filedialog.askopenfile(filetypes=(("PoitClouds", "*.ply;*.pts;*.e57"), ("All files", "*.*")))
        fullpath = str(fullpath)
        
        if 'v2' in resulting_mesh_type:
            
            face_number = 900000
            designator = 'hr_'
            folder_type = 'HighRes'
            folder_suffix = '_hr'
            texture_size = 8192             

        else: #If type is not v2, we assume the mesh will be for hololens (v1)
            
            face_number = 150000
            designator = 'lr_'
            folder_type = 'LowRes'
            folder_suffix = '_lr'
            texture_size = 8192            
        
        
        # Here we will include the start of the loop
        
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

        lat = "0"
        lon = "0"

        # We will encode the lat and lon into utm compliant coordinates for the xyz file and retrieve the utm zone for the prj file

        utm_easting, utm_northing, zone, zone_letter = utm.from_latlon(float(lat), float(lon))
        utm_easting = "%.2f" % utm_easting
        utm_northing = "%.2f" % utm_northing

        # Separate source path from filename
        path, filename = os.path.split(fullpath)
        path = path.replace("<_io.TextIOWrapper name='", '')
        filename = filename.replace("' mode='r' encoding='cp1252'>", '')

        fullpath = path + separator + filename

        if 'None' in fullpath:
            quit()

        if '.e57' in fullpath:
            fullpath, mesh_depth = self.load_e57(fullpath)

        path, filename = os.path.split(fullpath)

        logfilename = filename.replace('.ply', '').replace('.pts', '').replace('.obj', '').replace('.e57', '')
        pc_folder = logfilename
        
        log_name = designator + filename.replace('.ply', '').replace('.pts', '').replace('.obj', '').replace('.e57', '') + "_" + str(d) + "_" + str(ct) + ".log"

        # Derive destination folders from source path
        post_dest_folder = "ARTAK_MM/POST/Lidar" + separator + designator + pc_folder + separator + "Data"
        model_dest_folder = "ARTAK_MM/POST/Lidar" + separator + designator + pc_folder + separator + "Data/Model"
        mesh_output_folder = "ARTAK_MM/DATA/PointClouds/"+folder_type + separator + pc_folder + separator + "mesh"+folder_suffix
        simplified_output_folder = "ARTAK_MM/DATA/PointClouds/"+folder_type + separator + pc_folder + separator + "simplified"+folder_suffix
        gen_path_folder = "ARTAK_MM/DATA/Generated_Mesh"
        with_texture_output_folder = "ARTAK_MM/DATA/PointClouds/"+folder_type + separator + pc_folder + separator + "final"+folder_suffix
        log_folder = "ARTAK_MM/LOGS/"

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

        if "lr_" in designator:
            # Create xyz and prj based on lat and lon provided
            prj_1 = 'PROJCS["WGS 84 / UTM zone '
            prj_2 = '",GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]],PROJECTION["Transverse_Mercator"],PARAMETER["latitude_of_origin",0],PARAMETER["central_meridian",-81],PARAMETER["scale_factor",0.9996],PARAMETER["false_easting",500000],PARAMETER["false_northing",0],UNIT["metre",1,AUTHORITY["EPSG","9001"]],AXIS["Easting",EAST],AXIS["Northing",NORTH],AUTHORITY["EPSG","32617"]]'

            with open(with_texture_output_folder + separator + logfilename + '.xyz', 'w') as xyz:
                xyz.write(str(utm_easting + " " + str(utm_northing) + " " + "101.000"))

            with open(with_texture_output_folder + separator + logfilename + '.prj', 'w') as prj:
                prj.write(str(prj_1) + str(zone) + str(prj_2))
                
        with open("ARTAK_MM/LOGS/status.log", "w") as status:
            status.write("running")        

        if ".obj" in filename:
            
            origin = 'obj'
            
            message = 'Loading OBJ. File: '+str(fullpath)
            log.info(message)            
            self.write_to_log(path, separator, message)
            shutil.copy(fullpath, simplified_output_folder)
            shutil.rmtree(mesh_output_folder)
            generated_mesh = fullpath
            self.mesh_processing(generated_mesh, texture_size, origin)           
            
        message = 'Loading PointCloud. File: ' + str(fullpath)
        log.info(message)
        self.write_to_log(path, separator, message)
        pcd = o3d.io.read_point_cloud(fullpath)

        # This will output the Point count
        log.info(str(pcd)+"\r")
        
        message = str(pcd)
        self.write_to_log(path, separator, message)
        self.downsample(pcd, texture_size)

    def downsample(self, pcd, texture_size):
        # We need to downsample the PointCloud to make it less dense and easier to work with
        message = "Downsampling."
        log.info(message)
        self.write_to_log(path, separator, message)
        message = str(pcd)
        downpcd = pcd.voxel_down_sample(voxel_size = 0.03)
        log.info(str(downpcd)+"\r")
        message = str(downpcd)
        self.write_to_log(path, separator, message)
        self.compute_normals_and_generate_mesh(downpcd, mesh_depth, texture_size)

    def compute_normals_and_generate_mesh(self, downpcd, mesh_depth, texture_size):

        # Since some PointClouds don't include normals information (needed for texture and color extraction) we will have to calculate it.
        message = 'Computing Normals.'
        log.info(message)
        self.write_to_log(path, separator, message)
        downpcd.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=30))

        log.info('Generating Mesh.')
        message = 'Generating Mesh.'
        self.write_to_log(path, separator, message)

        mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(downpcd, depth=mesh_depth, width=0, scale=1.1,
                                                                         linear_fit=False)[0]
        generated_mesh = mesh_output_folder + separator + filename.replace('ply', 'obj').replace('pts', 'obj')

        message = 'Exporting Mesh.'
        log.info(message)
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
        origin = 'pc'

        if mesh_file_size > 10000000000:
            
            mesh_depth = 10
            message = 'Mesh is not memory friedly. Retrying with safer parameters.'
            log.info(message)
            self.write_to_log(path, separator, message)
            self.compute_normals_and_generate_mesh(downpcd, mesh_depth, texture_size, origin)

        else:
            self.mesh_processing(generated_mesh, texture_size, origin)

    def mesh_processing(self, generated_mesh, texture_size, origin):

        try:
            
            # We will use Meshlab from now on to to handle the processing.
            ms = pymeshlab.MeshSet()
            message = 'Analyzing.'
            log.info(message)
            self.write_to_log(path, separator, message)
            ms.load_new_mesh(generated_mesh)
            
            if 'obj' in origin:
                
                newpath = generated_mesh
                message = 'Bypassing Mesh Refinement.'
                log.info(message)
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
    
                    p = pymeshlab.PercentageValue(25)
                    message = 'Refining'
                    log.info(message)
                    self.write_to_log(path, separator, message)
                    # We will select faces that are long based on the bounding box calculation and then remove them
                    ms.apply_filter('compute_selection_by_edge_length',
                                    threshold=t_hold)
                    ms.apply_filter('meshing_remove_selected_faces')
                    # The selection process and removal of long faces will create floaters, we will remove isolated faces
                    ms.apply_filter('meshing_remove_connected_component_by_diameter',
                                    mincomponentdiag = p)
                    # if this is a generated file from exyn sensors, then we need to use 'safe' values different from the leica ones.
    
                    if ".ply" in filename:
                        t_hold = 0.36
    
                    elif ".pts" in filename:
                        t_hold = 0.1
    
                    else:
                        t_hold = 0.1
    
                    # Since there will still be some long faces, we will mark them and remove them, this time applying a 0.06 thershold. This is
                    ms.apply_filter('compute_selection_by_edge_length',                        threshold=t_hold)
                    ms.apply_filter('meshing_remove_selected_faces')
                    # Then we remove any isolated faces (floaters) that might still be laying around
                    ms.apply_filter('meshing_remove_connected_component_by_diameter',
                                    mincomponentdiag=p)
                    message = 'Exporting Mesh.'
                    log.info(message)
                    self.write_to_log(path, separator, message)
    
                    newpath = simplified_output_folder + separator + filename.replace('ply', 'obj').replace('pts', 'obj')
                    newpath_gen = gen_path_folder + separator + filename.replace('ply', 'obj').replace('pts', 'obj')
                    
                    ms.save_current_mesh(newpath,
                                         save_vertex_color=True,
                                         save_vertex_coord=True,
                                         save_vertex_normal=True,
                                         save_face_color=True,
                                         save_wedge_texcoord=True,
                                         save_wedge_normal=True,
                                         save_polygonal=True)
                    
                    shutil.copyfile(newpath, newpath_gen)
    
                except pymeshlab.pmeshlab.PyMeshLabException:
    
                    try:
    
                        ms.load_new_mesh(generated_mesh)
                        log.warning('Mesh not optimal. Retargeting parameters (1).\r')
                        message = 'Mesh not optimal. Retargeting parameters (1).'
                        self.write_to_log(path, separator, message)
    
                        boundingbox = ms.current_mesh().bounding_box()
                        diag = boundingbox.diagonal()
                        t_hold = diag / 200
    
                        p = pymeshlab.PercentageValue(25)
    
                        log.info('Refining.')
                        message = 'Refining'
                        self.write_to_log(path, separator, message)
    
                        # We will select faces that are long based on the bounding box calculation and then remove them
                        ms.apply_filter('compute_selection_by_edge_length',
                                        threshold=t_hold)
                        ms.apply_filter('meshing_remove_selected_faces')
    
                        # The selection process and removal of long faces will create floaters, we will remove isolated faces
                        ms.apply_filter('meshing_remove_connected_component_by_diameter',
                                        mincomponentdiag=p)
    
                        if ".ply" in filename:
                            t_hold = 0.6
    
                        elif ".pts" in filename:
                            t_hold = 0.2
    
                        else:
                            t_hold = 0.2
    
                        # Since there will still be some long faces, we will mark them and remove them, this time applying a 0.06 thershold. This is
                        ms.apply_filter('compute_selection_by_edge_length',
                                        threshold=t_hold)
                        ms.apply_filter('meshing_remove_selected_faces')
    
                        # Then we remove any isolated faces (floaters) that might still be laying around
                        ms.apply_filter('meshing_remove_connected_component_by_diameter',
                                        mincomponentdiag = p)
    
                        message = 'Exporting Mesh.'
                        
                        newpath = simplified_output_folder + separator + filename.replace('ply', 'obj').replace('pts', 'obj')
                        newpath_gen = gen_path_folder + separator + filename.replace('ply', 'obj').replace('pts', 'obj')
                        
                        ms.save_current_mesh(newpath,
                                             save_vertex_color=True,
                                             save_vertex_coord=True,
                                             save_vertex_normal=True,
                                             save_face_color=True,
                                             save_wedge_texcoord=True,
                                             save_wedge_normal=True,
                                             save_polygonal=True)
                        
                        shutil.copyfile(newpath, newpath_gen)
    
                    except pymeshlab.pmeshlab.PyMeshLabException:
    
                        try:
    
                            ms.load_new_mesh(generated_mesh)
                            log.warning('Mesh not optimal. Retargeting parameters (2).\r')
                            message = 'Mesh not optimal. Retargeting parameters (2).'
                            self.write_to_log(path, separator, message)
                            boundingbox = ms.current_mesh().bounding_box()
                            diag = boundingbox.diagonal()
                            t_hold = diag / 200
                            p = pymeshlab.PercentageValue(10)
                            log.info('Refining.')
                            message = 'Refining'
                            self.write_to_log(path, separator, message)
                            # We will select faces that are long based on the bounding box calculation and then remove them
                            ms.apply_filter('compute_selection_by_edge_length',
                                            threshold=t_hold)
                            ms.apply_filter('meshing_remove_selected_faces')
    
                            # The selection process and removal of long faces will reate floaters, we will remove isolated faces
                            ms.apply_filter('meshing_remove_connected_component_by_diameter',
                                            mincomponentdiag=p)
    
                            t_hold = 0.9 #threshold will be the same for all if it gets this far
    
                            # Since there will still be some long faces, we will mark them and remove them, this time applying a 0.06 thershold. This is
                            ms.apply_filter('compute_selection_by_edge_length',
                                            threshold=t_hold)
                            ms.apply_filter('meshing_remove_selected_faces')
                            # Then we remove any isolated faces (floaters) that might still be laying around
                            ms.apply_filter('meshing_remove_connected_component_by_diameter',
                                            mincomponentdiag=p)
                            log.info("Exporting Mesh.")
                            message = 'Exporting Mesh.'
                            self.write_to_log(path, separator, message)
    
                            newpath = simplified_output_folder + separator + filename.replace('ply', 'obj').replace('pts', 'obj')
                            newpath_gen = gen_path_folder + separator + filename.replace('ply', 'obj').replace('pts', 'obj')
                            
                            ms.save_current_mesh(newpath,
                                                 save_vertex_color=True,
                                                 save_vertex_coord=True,
                                                 save_vertex_normal=True,
                                                 save_face_color=True,
                                                 save_wedge_texcoord=True,
                                                 save_wedge_normal=True,
                                                 save_polygonal=True)
                            
                            shutil.copyfile(newpath, newpath_gen)
    
                        except pymeshlab.pmeshlab.PyMeshLabException:
    
                            # Cleanup
                            try:
                                shutil.rmtree("ARTAK_MM/DATA/PointClouds/" + folder_type + separator + pc_folder)
                            # Remove the status flag for MM_GUI progressbar
                            except FileNotFoundError:
                                pass
                            
                            with open(log_folder + "status.log", "w") as status:
                                status.write("error")
 
                            message = 'Could not compute Mesh from PointCloud. Aborting.'
                            self.write_to_log(path, separator, message)
                            
                            log.error(message)
                            log.error('Process terminated.')
      
                            # Announce error and terminate.
                            messagebox.showerror('ARTAK 3D Map Maker', 'Could not compute Mesh from PointCloud. Aborting.')
                            
                            sys.exit()  
 
            m = ms.current_mesh()
            v_number = m.vertex_number()
            f_number = m.face_number()
            log.info("Overall Target FC: "+str(face_number)+".\r")
            log.info("Initial VC: "+str(v_number)+". Initial FC: "+str(f_number)+".\r")
            message = 'Initial VC: ' + str(v_number) + '. Initial FC: ' + str(f_number) + "."
            self.write_to_log(path, separator, message)

            # Let's take a look at the mesh file to see how big it is. We are constrained to about 120Mb in this case, therefore we
            # will have to decimate if the file is bigger than that number.

            # if f_number > 6500000:  # Decimate over 6500000 faces (approx.650Mb)
            if f_number > face_number:  # Decimate over 6500000 faces (approx.950Mb)
                
                self.decimation(ms, newpath, f_number, texture_size)

            else:
                
                newpath1 = simplified_output_folder + separator + 'decimated_' + filename.replace('ply', 'obj').replace('pts', 'obj')

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
                
            log.error('Not enough Memory to run the process. Quitting.\r')
            message = 'Error. Not enough Memory to run the process. Quitting.'
            self.write_to_log(path, separator, message)
            sys.exit()

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
            log.info("Target: "+str(int(target_faces))+" F. Iter. "+str(c)+".\r")
            message = "Target: " + str(int(target_faces)) + " F. Iter. " + str(c) + "."
            self.write_to_log(path, separator, message)
            ms.apply_filter('meshing_decimation_quadric_edge_collapse',
                            targetfacenum=int(target_faces), targetperc=0,
                            qualitythr=0.3,
                            optimalplacement=True,
                            preservenormal=True,
                            autoclean=True)
            f_number = m.face_number()
            v_number = m.vertex_number()
            ratio = (abs(target_faces / f_number) - 1.1) * 10  # Efficiency ratio. resulting amt faces vs target amt of faces
            log.info("Achieved: "+str(f_number)+" F. Ratio ==> "+"%.2f" % abs(ratio)+":1.00.\r")
            message = 'Achieved: ' + str(f_number) + ' F. Ratio ==> ' + '%.2f' % abs(ratio) + ':1.00.'
            self.write_to_log(path, separator, message)
            c += 1

        m = ms.current_mesh()
        f_number = m.face_number()
        v_number = m.vertex_number()

        log.info("End VC: "+str(v_number)+". End FC: "+str(f_number)+".\r")
        message = 'End VC: ' + str(v_number) + '. End FC: ' + str(f_number) + "."
        self.write_to_log(path, separator, message)

        newpath1 = simplified_output_folder + separator + 'decimated_' + filename.replace('ply', 'obj').replace(
            'pts',
            'obj')

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

        message = 'Generating Texture and Materials.'
        log.info(message)
        self.write_to_log(path, separator, message)

        ms.load_new_mesh(newpath)
        ms.load_new_mesh(newpath1)

        message = 'Texturing to '+str(texture_size)+'px x '+str(texture_size)+'px Resolution.'
        log.info(message)
        self.write_to_log(path, separator, message)
        
        try:
            
            if 'v2' in resulting_mesh_type:
                itb = 3 #Need to change this to a lower value to avoind itb overrun
                
            else:
                itb = 3
        
            ms.apply_filter('compute_texcoord_parametrization_triangle_trivial_per_wedge',
                            sidedim = 0,
                            textdim = texture_size,
                            border = itb,
                            method = 'Basic')
            
        except pymeshlab.pmeshlab.PyMeshLabException:
            
            # Announce error and terminate.
            
            with open(log_folder + "status.log", "w") as status:
                status.write("error")            
                
            log.error('ITB overrun. Quitting.')
            message = 'Error. ITB overrun. Quitting.'
            self.write_to_log(path, separator, message)
            messagebox.showerror('ARTAK 3D Map Maker', 'Could not compute Mesh from PointCloud. Aborting.')
            sys.exit()            
            
        percentage = pymeshlab.PercentageValue(2)

        newpath_texturized = with_texture_output_folder + separator + filename.replace('ply', 'obj').replace('pts','obj').replace('decimated_', '')

        model_path = model_dest_folder + separator + 'Model.obj'

        #Here we transfer the texture
        ms.apply_filter('transfer_attributes_to_texture_per_vertex',
                         sourcemesh = 0,
                         targetmesh  = 1,
                         attributeenum = 0,
                         upperbound = percentage,
                         textname = 'texture.png',
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

        # We need to compress the texture file
        img = Image.open(with_texture_output_folder + separator + 'texture.png')
        img = img.convert("P", palette=Image.WEB, colors = 256)
        img.save(with_texture_output_folder + separator + 'texture.png', optimize=True)
        img.save(model_dest_folder + separator +  'texture.png', optimize=True)

        # Let's compress
        self.compress_into_zip(with_texture_output_folder, newpath)
        files = [f for f in glob.glob(with_texture_output_folder + "/*.zip")]
        for file in files:
            shutil.copy(file, post_dest_folder)

        # Cleanup finish

        try:
            shutil.rmtree("ARTAK_MM/DATA/PointClouds/" + folder_type + separator + pc_folder)
            # Remove the status flag for MM_GUI progressbar
        except FileNotFoundError:
            pass

        with open(log_folder + "status.log", "w") as status:
            status.write("done")
            
        if "True" in auto_open:
            
            self.open_obj_model(model_dest_folder)
            
        message = 'Reconstruction Complete.'
        log.info(message)
        self.write_to_log(path, separator, message)
        messagebox.showinfo('ARTAK 3D Map Maker', 'Reconstruction Complete.')
        sys.exit()

    def compress_into_zip(self, with_texture_output_folder, newpath):

        if 'lr_' in designator:
            extensions = ['.obj', '.obj.mtl', '.xyz', '.prj']
        else:
            extensions = ['.obj', '.obj.mtl', '.png']

        compression = zipfile.ZIP_DEFLATED
        zip_file = with_texture_output_folder + separator + filename.replace('.obj', '').replace('.ply',
                                                                                                         '').replace(
            '.pts', '') + '.zip'
        with zipfile.ZipFile(zip_file, mode="w") as zf:
            for ext in extensions:
                try:
                    zf.write(with_texture_output_folder + separator + filename.replace('.obj', '').replace('.ply','').replace('.pts', '') + ext, filename.replace('.obj', '').replace('.ply', '').replace('.pts', '') + ext,
                             compress_type = compression, compresslevel = 9)
                except FileExistsError:
                    pass
                except FileNotFoundError:
                    pass
            zf.write(with_texture_output_folder + separator + 'texture.png', 'texture.png', compress_type = compression, compresslevel = 9)

        return

    def write_to_log(self, path, separator, message):

        with open(log_folder + log_name, "a+") as log_file:
            log_file.write(str(datetime.now())+" "+message + "\r")
        return
    
    def open_obj_model(self, model_dest_folder):
        
        model_name = os.path.join(model_dest_folder, "Model.obj")
        model = o3d.io.read_triangle_mesh(model_name)
        material = o3d.visualization.rendering.MaterialRecord()
        material.shader = "defaultLit"        
        
        albedo_name = os.path.join(model_dest_folder, "texture.png")
        material.albedo_img = o3d.io.read_image(albedo_name)
        
        o3d.visualization.draw([{"name": "Model", "geometry": model, "material": material}], title = "ARTAK 3D Map Maker || LiDAR Edition", bg_color = [0,0,0,0], show_skybox = False, actions = None, width = 1280, height = 900)
        
        return
    
if __name__ == '__main__':
    meshing().get_PointCloud()