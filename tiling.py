'''
import open3d as o3d
import os, sys, shutil

fullpath = input("Full path: ")
fullpath = fullpath.replace('"', '')

#get paths
base_path, base_filename = os.path.split(fullpath)
file_name, extension = os.path.splitext(base_filename)
downsampled_file = file_name+"_ds"+extension
downsampled_fullpath = os.path.join(base_path, downsampled_file)
tiles_folder = os.path.join(base_path, file_name)

#read the input cloud
print("Loading PC.")
pcd = o3d.io.read_point_cloud(fullpath)

#downsample and export
print("Downsampling.")
downpcd = pcd.voxel_down_sample(voxel_size = 0.05)
print("Exporting.")
o3d.io.write_point_cloud(downsampled_fullpath,
                         downpcd,
                         write_ascii = False)
#tile
print("Generating tiles.")
cmd = "py3dtiles convert "+downsampled_fullpath+" --out "+ tiles_folder+" --srs_in 4979 -v"
#cmd = "gocesiumtiler file -o "+ tiles_folder +" -e 4979 -r 5 -m 1000 -d 20 "+ downsampled_fullpath
os.system(cmd)

#zip
print("Archiving.")
shutil.make_archive(tiles_folder, 'zip', tiles_folder)

#cleanup
shutil.rmtree(tiles_folder)
os.remove(downsampled_fullpath)

sys.exit()


import os, sys, shutil
import pyCloudCompare as cc

fullpath = input("Full path: ")
fullpath = fullpath.replace('"', '')
path, filename = os.path.split(fullpath)
file, extension = os.path.splitext(filename)
las_filename = file+".las"
new_fullpath_las = os.path.join(path, las_filename)
tiles_folder = os.path.join(path, las_filename.replace(".las", ''))
print("Converting to .las format.")
cli = cc.CloudCompareCLI()
cmd = cli.new_command()
cmd.silent()  # Disable console
cmd.open(fullpath)  # Read file
cmd.cloud_export_format(cc.CLOUD_EXPORT_FORMAT.LAS, extension="las")
cmd.save_clouds(new_fullpath_las)
print(cmd)
cmd.execute()
print("Generating tiles.")
cmd = "gocesiumtiler file -o "+ tiles_folder +" -e 4978 -g -r 5 -m 1000 -d 20  "+ new_fullpath_las
os.system(cmd)
print("Creating zip file.")
shutil.make_archive(tiles_folder, 'zip', tiles_folder)

#cleanup
shutil.rmtree(tiles_folder)
os.remove(new_fullpath_las)
print("Done.")
sys.exit()

#------------------------------------------------------

import open3d as o3d
import os, sys, shutil
import pyCloudCompare as cc

ply_point_cloud = o3d.data.PLYPointCloud()
fullpath = input("Full path: ")
print("Loading PC.")
fullpath = fullpath.replace('"', '')

pcd = o3d.io.read_point_cloud(fullpath)

path, filename = os.path.split(fullpath)
file, extension = os.path.splitext(filename)
file = file+'_ds'
filename = file+extension
las_filename = file+".las"
new_fullpath = os.path.join(path, filename)
new_fullpath_las = os.path.join(path, las_filename)
tiles_folder = os.path.join(path, las_filename.replace(".las", ''))
#tiles_folder = os.path.join(path, filename.replace(".ply", '').replace("_ds", ''))

print("Downsampling.")
downpcd = pcd.voxel_down_sample(voxel_size = 0.02)
print("Exporting.")
o3d.io.write_point_cloud(new_fullpath,
                         downpcd,
                         write_ascii = True)


print("Converting to .las format.")
cli = cc.CloudCompareCLI()
cmd = cli.new_command()
cmd.silent()  # Disable console
cmd.open(new_fullpath)  # Read file
#cmd.open(fullpath)  # Read file
cmd.cloud_export_format(cc.CLOUD_EXPORT_FORMAT.LAS, extension="las")
cmd.save_clouds(new_fullpath_las.replace("_ds", ''))
#cmd.save_clouds(new_fullpath_las)
print(cmd)
cmd.execute()

print("Generating tiles.")
cmd = "gocesiumtiler file -o "+ tiles_folder.replace("_ds", '') +" -e 4978 -g -r 5 -m 1000 -d 20 "+ new_fullpath_las.replace("_ds", '')
#cmd = "gocesiumtiler file -o "+ tiles_folder +" -e 4978 -g -r 10 -m 1000 -d 12 "+ new_fullpath_las
#cmd = "gocesiumtiler file -o "+ tiles_folder.replace("_ds", '') +" -e 4978 "+ new_fullpath_las.replace("_ds", '')
#cmd = "gocesiumtiler file -o "+ tiles_folder +" -e 4978 "+ new_fullpath_las
#cmd = "py3dtiles convert "+new_fullpath.replace('_ds', '')+" --out "+ tiles_folder.replace('_ds', '')+" --srs_in 4978 -v"
os.system(cmd)
print("Creating zip file.")
shutil.make_archive(tiles_folder.replace('_ds', ''), 'zip', tiles_folder.replace('_ds', ''))
#cleanup
shutil.rmtree(tiles_folder.replace('_ds', ''))
os.remove(new_fullpath)
os.remove(new_fullpath_las.replace('_ds', ''))
print("Done.")
sys.exit()

#---------------------------------------------------------
'''

import os, sys, shutil

fullpath = input("Full path: ")
print("Loading PC.")
fullpath = fullpath.replace('"', '')
path, filename = os.path.split(fullpath)
file, extension = os.path.splitext(filename)
tiles_folder = os.path.join(path, filename.replace(".ply", ''))

print("Generating tiles.")
cmd = "py3dtiles convert "+fullpath+" --out "+ tiles_folder+" --srs_in 4979 -v"
os.system(cmd)
print("Zipping.")
shutil.make_archive(tiles_folder, 'zip', tiles_folder)
#cleanup
shutil.rmtree(tiles_folder)
print("Done.")
sys.exit()

'''

import open3d as o3d
import os, sys, shutil
import pyCloudCompare as cc

fullpath = input("Full path: ")
fullpath = fullpath.replace('"', '')

#generate paths
base_path, base_filename = os.path.split(fullpath)
file_name, extension = os.path.splitext(base_filename)
downsampled_file = file_name+"_ds"+extension
las_file = file_name+".las"
downsampled_fullpath = os.path.join(base_path, downsampled_file)
las_filepath = os.path.join(base_path, las_file)
tiles_folder = os.path.join(base_path, file_name)

#read the input cloud
print("Loading PC.")
pcd = o3d.io.read_point_cloud(fullpath)

#downsample and export
print("Downsampling.")
downpcd = pcd.voxel_down_sample(voxel_size = 0.02)
o3d.io.write_point_cloud(downsampled_fullpath,
                         downpcd,
                         write_ascii = False)

print("Converting to .las format.")
cli = cc.CloudCompareCLI()
cmd = cli.new_command()
cmd.silent()  # Disable console
cmd.open(downsampled_fullpath)  # Read file
cmd.cloud_export_format(cc.CLOUD_EXPORT_FORMAT.LAS, extension="las")
cmd.save_clouds(las_filepath.replace("_ds", ''))
print(cmd)
cmd.execute()

#tiling
print("Generating tiles.")
cmd = "gocesiumtiler file -o "+ tiles_folder +"-epsg 4978 "+ las_filepath.replace("_ds", '')
os.system(cmd)

#zip
print("Archiving.")
shutil.make_archive(tiles_folder, 'zip', tiles_folder)

#cleanup
shutil.rmtree(tiles_folder)
os.remove(downsampled_fullpath)
os.remove(las_filepath.replace("_ds", ''))
print("Done.")
sys.exit()

'''
