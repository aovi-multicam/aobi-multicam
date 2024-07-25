import open3d as o3d  
import numpy as np  
from scipy.spatial.transform import Rotation as R  
import copy  # 导入copy模块
  
def load_ply(file_path):  
    pcd = o3d.io.read_point_cloud(file_path)  
    return pcd  
  
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
  
# 加载点云  
pcd1 = load_ply("E://output//pointcloud//1721807224302//RGBDPoints_1721807224302.ply")  
pcd2 = load_ply("E://output//pointcloud//l//RGBDPoints_1721807265845.ply")  
  
# 假设的旋转角度（以度为单位）和平移向量（以米为单位）  
#euler_angles = np.array([-0.0077, -0.1641, -0.0065])  # 注意这里的顺序可能需要根据你的实际情况调整 
#euler_angles = np.array([-0.4414, -9.4, -0.37]) 
euler_angles = np.array([0, 47, 0]) 
#translation_vector = np.array([508.7920, 1.2722, 531.4581]) / 1000.0  # 修正了第三个值  
translation_vector = np.array([-550000, 1.2722, 153141]) / 1000.0
# 创建变换矩阵  
transform_matrix = create_transform_matrix(euler_angles, translation_vector)  
  
# 对第二个点云进行变换  
pcd2_transformed = copy.deepcopy(pcd2)  # 使用deepcopy来复制pcd2  
transform_pcd(pcd2_transformed, transform_matrix) 
  
# 拼接点云  
merged_pcd = concatenate_point_clouds([pcd1, pcd2_transformed])  
  
# 可视化结果  
o3d.visualization.draw_geometries([merged_pcd])