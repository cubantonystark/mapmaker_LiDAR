from pyntcloud import PyntCloud

human_face = PyntCloud.from_file("D:/Projects/MapMaker_Lidar/build/v1.0.5/ARTAK_MM/DATA/Generated_PointClouds/exyn_mine_interior.ply")

human_face.plot()