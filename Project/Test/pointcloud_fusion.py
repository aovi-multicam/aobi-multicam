import open3d as o3d  
import numpy as np  
from scipy.spatial.transform import Rotation as R  
import copy  # 导入copy模块
import os
import os.path
from plyfile import PlyData, PlyElement
# 点云存放路径文件夹
point_cloud_save_dir = "E:\\Project\\SZUer-explode-XiAn\\aobi-multicam\\Project\\Test\\pointclouds"
merged_point_clouds_save_dir = "E:\\Project\\SZUer-explode-XiAn\\aobi-multicam\\Project\\Test\\merged_point_clouds"


def load_ply(file_path):  
    pcd = o3d.io.read_point_cloud(file_path)  
    return pcd  
  
def load_point_clouds_from_folder(folder_path):
    point_clouds = []
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.ply'):  # 根据需要调整文件扩展名
            file_path = os.path.join(folder_path, file_name)
            pcd = o3d.io.read_point_cloud(file_path)
            point_clouds.append(pcd)
            print('加载点云文件：' + file_path)
    return point_clouds


def create_transform_matrix(euler_angles, translation_vector):  
    # 将欧拉角从度转换为弧度  
    euler_radians = np.radians(euler_angles)  
    # 使用scipy的Rotation类从欧拉角创建旋转矩阵  
    rot_matrix = R.from_euler('zyx', euler_radians, degrees=False).as_matrix()  # 注意这里的'zyx'顺序可能需要根据实际情况调整  
    # 创建齐次变换矩阵  
    transform_matrix = np.eye(4)  
    transform_matrix[:3, :3] = rot_matrix  
    transform_matrix[:3, 3] = translation_vector  
    return transform_matrix  
  
def transform_pcd(pcd, transform):  
    pcd.transform(transform)  
  
def concatenate_point_clouds(pcds):  
    merged_pcd = pcds[0]  
    for i in range(1, len(pcds)):  
        merged_pcd += pcds[i]  
    return merged_pcd  
  

def save_point_cloud(pcd, file_path):
    o3d.io.write_point_cloud(file_path, pcd)


# 加载点云 

# 加载点云列表
point_cloads_list = load_point_clouds_from_folder(point_cloud_save_dir)
translation_vector_list = [np.array([-1060,0,440]),np.array([-1500,0,1500]),np.array([-1060,0,440+1060*2]),
                           np.array([0,0,3100]),np.array([1060,0,440+1060*2]),np.array([1500,0,1500]),
                           np.array([1060,0,440])]
i = 0
for pcd in point_cloads_list:
    if i == 0:
        merged_pcd = pcd
        i = i + 1
        continue
    # 假设的旋转角度（以度为单位）和平移向量（以米为单位）  
    #euler_angles = np.array([-0.0077, -0.1641, -0.0065])  # 注意这里的顺序可能需要根据你的实际情况调整 
    #euler_angles = np.array([-0.4414, -9.4, -0.37]) 
    euler_angles = np.array([0, 45*i, 0]) 
    #translation_vector = np.array([508.7920, 1.2722, 531.4581]) / 1000.0  # 修正了第三个值  
    translation_vector = translation_vector_list[i-1]
    # 创建变换矩阵  
    transform_matrix = create_transform_matrix(euler_angles, translation_vector)  
    
    # 对第二个点云进行变换  
    pcd2_transformed = copy.deepcopy(pcd)  # 使用deepcopy来复制pcd2  
    transform_pcd(pcd2_transformed, transform_matrix) 
    
    # 拼接点云  
    merged_pcd = concatenate_point_clouds([merged_pcd, pcd2_transformed]) 
    print('第' + str(i) + '个点云拼接完成')
    i = i + 1
    # 可视化结果  
o3d.visualization.draw_geometries([merged_pcd])  

# 保存变换后的点云

points_filename = os.path.join(merged_point_clouds_save_dir, f"merged_pcd.ply")
# 将 merged_pcd 转换为 numpy 数组
points = np.asarray(merged_pcd.points)

# 创建适合 PlyElement.describe 的结构化数组
vertex = np.array([(point[0], point[1], point[2]) for point in points],
                  dtype=[('x', 'f4'), ('y', 'f4'), ('z', 'f4')])

# 创建 PlyElement
el = PlyElement.describe(vertex, 'vertex')

# 保存 PlyData
PlyData([el], text=True).write(points_filename)
print('点云保存完成')

