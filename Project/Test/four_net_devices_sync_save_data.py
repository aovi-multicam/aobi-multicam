# ******************************************************************************
#  Copyright (c) 2023 Orbbec 3D Technolo
# gy, Inc
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

# ******************************************************************************

import json  # 导入json模块，用于处理JSON格式的数据
import os  # 导入os模块，提供与操作系统交互的功能，如文件路径操作  
import time  # 导入time模块，提供与时间相关的函数 
from queue import Queue  # 从queue模块导入Queue类，用于创建线程安全的队列  
from threading import Lock # 从threading模块导入Lock类，用于实现线程间的同步
from typing import List # 从typing模块导入List，用于类型注解，表示列表类型

import cv2 # 导入OpenCV库，用于图像处理
import numpy as np  # 导入numpy库，用于高效的数组和矩阵运算 
import open3d as o3d  # 导入Open3D库，用于处理3D数据和点云

from pyorbbecsdk import * # 从pyorbbecsdk模块导入所有内容，pyorbbecsdk是与Orbbec摄像头交互的SDK  
from utils import frame_to_bgr_image  # 从utils模块导入frame_to_bgr_image函数，该函数可能用于将帧转换为BGR格式的图像  


from plyfile import PlyData, PlyElement
# 定义一个全局锁，用于保护frames_queue的访问，确保线程安全
frames_queue_lock = Lock()

# Configuration settings
MAX_DEVICES = 4 # 允许连接的最大设备数量
MAX_QUEUE_SIZE = 5  # 每个设备帧队列的最大容量 
ESC_KEY = 27  # ESC键的ASCII码，用于检测用户是否希望退出程序
# 设置保存点云、深度图像和彩色图像的目录路径  
save_points_dir = os.path.join(os.getcwd(), "point_clouds")  # 点云数据保存目录
save_depth_image_dir = os.path.join(os.getcwd(), "depth_images") # 深度图像保存目录
save_color_image_dir = os.path.join(os.getcwd(), "color_images") # 彩色图像保存目录
#save_color_image_dir = "E:\\color_images"

frames_queue: List[Queue] = [Queue() for _ in range(MAX_DEVICES)]# 初始化frames_queue列表，为每个可能的设备创建一个队列 
stop_processing = False   # 定义一个全局标志，用于控制是否停止处理帧
curr_device_cnt = 4    # 当前设备计数器，用于在多个设备间分配帧队列

# Load config file for multiple devices    加载多设备同步配置文件
#config_file_path = os.path.join(os.path.dirname(__file__), "e:\\1-实习\\奥比\\Github_change\\aobi-multicam//config/multi_device_sync_config.json")  # 配置文件路径

config_file_path = os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    "../config/multi_device_sync_config.json",
)
multi_device_sync_config = {}  # 初始化一个空字典，用于存储配置文件的内容 


def convert_to_o3d_point_cloud(points, colors=None):   #将给定的点和颜色数据从NumPy 数组的形式转换为 Open3D 的点云（PointCloud）对象
    """
    Converts numpy arrays of points and colors (if provided) into an Open3D point cloud object.
    """
    pcd = o3d.geometry.PointCloud()  # 创建一个空的Open3D点云对象
    pcd.points = o3d.utility.Vector3dVector(points)  # 将numpy的点数组转换为Open3D的Vector3dVector并赋值给点云对象的点  
    if colors is not None:  # 如果提供了颜色信息
        pcd.colors = o3d.utility.Vector3dVector(colors / 255.0)  # Assuming colors are in [0, 255] 
        #将numpy的颜色数组（假设颜色值在[0, 255]范围内）转换为Open3D的Vector3dVector并赋值给点云对象的颜色
        # 颜色值被除以255.0以转换到[0.0, 1.0]范围，这是Open3D期望的颜色值范围
    return pcd  # 返回创建好的点云对象


def read_config(config_file: str):  #用于获取配置，接受一个字符串参数config_file，这个参数预期是一个配置文件的路径。
    global multi_device_sync_config   #声明一个全局变量multi_device_sync_config,如果multi_device_sync_config在函数外部没有被定义，这将会导致错误。
    with open(config_file, "r") as f:  #open只需要指定两个参数，一个是文件，另一个是模式，这里是以只读模式“r”打开config_file指定的文件，f是文件对象的引用
        #with语句可以确保文件在使用后正确关闭，即使在读取或写入文件时发生异常也是如此,将这个文件对象赋值给F，这样就可以在with语句块内部通过f来引用这个文件对象了。
        config = json.load(f)   #调用json.load(f)来解析文件f中的JSON数据，将结果存储在变量config中。
    for device in config["devices"]:  #遍历config字典中"devices"键对应的列表。每个device都是一个字典，代表一个设备的配置。
        multi_device_sync_config[device["serial_number"]] = device  #将每个设备的配置存储在全局变量multi_device_sync_config中，使用设备的序列号（serial_number）作为键。
        print(f"Device {device['serial_number']}: {device['config']['mode']}")  #打印每个设备的序列号和其配置中的mode。


def sync_mode_from_str(sync_mode_str: str) -> OBMultiDeviceSyncMode:  #函数接受一个字符串参数sync_mode_str，并返回一个名为OBMultiDeviceSyncMode的类型。
    sync_mode_str = sync_mode_str.upper()   #将输入的字符串转换为大写，以进行不区分大小写的比较。
    if sync_mode_str == "FREE_RUN":  #一系列的条件判断，将字符串映射到OBMultiDeviceSyncMode枚举的相应成员。
        return OBMultiDeviceSyncMode.FREE_RUN
    elif sync_mode_str == "STANDALONE":  #独立
        return OBMultiDeviceSyncMode.STANDALONE
    elif sync_mode_str == "PRIMARY":  #主要
        return OBMultiDeviceSyncMode.PRIMARY
    elif sync_mode_str == "SECONDARY": #从机
        return OBMultiDeviceSyncMode.SECONDARY
    elif sync_mode_str == "SECONDARY_SYNCED":  #二级已同步
        return OBMultiDeviceSyncMode.SECONDARY_SYNCED
    elif sync_mode_str == "SOFTWARE_TRIGGERIN":   #软件触发
        return OBMultiDeviceSyncMode.SOFTWARE_TRIGGERING
    elif sync_mode_str == "HARDWARE_TRIGGERING":  #硬件触发
        return OBMultiDeviceSyncMode.HARDWARE_TRIGGERING
    else:
        raise ValueError(f"Invalid sync mode: {sync_mode_str}")  #如果都不匹配则抛出一个ValueError异常，并附带一个描述性消息
        #raise语句用于抛出一个指定的异常,在这个例子中，它抛出了一个ValueError异常


# Frame processing and saving  #帧处理和保存，通常用于从多个摄像头设备中捕获并保存颜色图像和深度图像
#这个函数被设计为在一个循环中运行，直到一个全局变量stop_processing被设置为True，表示应该停止处理帧。
def process_frames(pipelines):  #参数pipelines预期是一个列表，包含了与每个摄像头设备相关联的处理管道（可能是用于配置摄像头或处理捕获到的帧的对象）。
    global frames_queue
    global stop_processing
    global curr_device_cnt, save_points_dir, save_depth_image_dir, save_color_image_dir
    #声明了将要使用的全局变量
    # frames_queue是一个队列或类似结构，用于存储从每个摄像头捕获的帧；
    # stop_processing是一个标志，用于控制是否继续处理帧；
    # curr_device_cnt是当前连接的摄像头设备数量；
    # save_points_dir
    # save_depth_image_dir、save_color_image_dir分别是用于保存深度图像和颜色图像的目录路径。
    while not stop_processing:  #使用while循环来不断处理帧，直到stop_processing为True。
        now = time.time()  #记录当前的时间
        for device_index in range(curr_device_cnt):  #以curr_device_cnt为值，range生成一个curr_device_cnt大小的序列，依次赋值给device_index，直到循环结束
            with frames_queue_lock:  #使用锁（frames_queue_lock）来安全地从对应设备的帧队列中获取帧。
                frames = frames_queue[device_index].get() if not frames_queue[device_index].empty() else None   # 尝试从指定设备的队列中获取帧，如果队列为空则返回None
            if frames is None:
                continue  #如果frames为None（即没有从队列中获取到帧），则跳过当前迭代，继续处理下一个设备或等待下一个循环迭代。
            color_frame = frames.get_color_frame() if frames else None  # 如果frames不为None，则获取彩色帧
            depth_frame = frames.get_depth_frame() if frames else None  # 如果frames不为None，则获取深度帧
            pipeline = pipelines[device_index]  #存储了与每个设备相关的处理管道  
            print(f"Device {device_index} frames")  # 打印正在处理哪个设备的帧

            if color_frame:
                color_image = frame_to_bgr_image(color_frame)  # 将彩色帧转换为BGR图像
                if color_image is not None and isinstance(color_image, np.ndarray):
                    if not os.path.exists(save_color_image_dir) :
                        os.mkdir(save_color_image_dir)
                color_filename = os.path.join(save_color_image_dir,    # 构造保存彩色帧的图像文件名 
                                              f"color_{device_index}_{color_frame.get_timestamp()}.png")
                cv2.imwrite(color_filename, color_image) # 使用OpenCV的cv2.imwrite函数保存图像 
                '''if cv2.imwrite(color_filename, color_image):  
                    print(f"Image saved successfully: {color_filename}")  
                else:  
                    print(f"Failed to save image: {color_filename}")  
            else:  
                print("color_image is not a valid image array")'''

            if depth_frame:    # 检查是否存在深度帧 
                timestamp = depth_frame.get_timestamp()  # 获取深度帧的时间戳
                width = depth_frame.get_width()  # 获取深度帧的宽度  
                height = depth_frame.get_height()  # 获取深度帧的高度  
                timestamp2 = depth_frame.get_timestamp_us()  #冗余项
                scale = depth_frame.get_depth_scale()  # 获取深度帧的缩放比例  
                data = np.frombuffer(depth_frame.get_data(), dtype=np.uint16)  # 从深度帧的原始数据中提取数据，并重新塑形为二维数组  
                #np.frombuffer是NumPy库中的一个函数，它用于从字节缓冲区（如字节对象或兼容的数组接口）中创建一个一维数组。
                #depth_frame.get_data()方法返回一个包含深度帧原始数据的字节缓冲区。这些原始数据通常是以某种格式（如16位无符号整数，即np.uint16）编码的深度值。
                data = data.reshape((height, width))
                #reshape是NumPy数组的一个方法，允许改变数组的形状而不改变其数据。在这个例子中将一维数组data重新塑形为二维数组，以匹配深度帧的宽度和高度。
                data = data.astype(np.float32) * scale  #将数据转换类型为np.float32，再乘以缩放比例
                data = data.astype(np.uint16)   #将数据转换类型为np.uint16
                
                if not os.path.exists(save_depth_image_dir):  # 检查保存深度帧原始数据的目录是否存在，如果不存在则创建 
                    os.mkdir(save_depth_image_dir)
                raw_filename = save_depth_image_dir +"/depth_{}x{}_device_{}_{}.raw".format(width, height,device_index, timestamp2)
                data.tofile(raw_filename)
                
                camera_param = pipeline.get_camera_param()  # 获取相机参数，并从frames中获取点云
                points = frames.get_point_cloud(camera_param)
                if len(points) == 0:
                    print("no depth points")
                    continue  # 检查点云是否为空,如果点云为空，输出并跳过后续的点云处理 
                points_array = np.array([tuple(point) for point in points],
                                        dtype=[('x', 'f4'), ('y', 'f4'), ('z', 'f4')])    # 将点云转换为NumPy数组，每个点都是一个包含x, y, z的元组，然后转换为结构化数组
                                        #每个字段的数据类型都是'f4'，即32位浮点数（在NumPy中，'f4'是np.float32的别名）。points_filename = save_points_dir + "/points_{}x{}_device_{}_{}.ply".format(width, height,device_index, timestamp)
                points_filename = os.path.join(save_points_dir, f"points_{timestamp}.ply")
                el = PlyElement.describe(points_array, 'vertex')
                PlyData([el], text=True).write(points_filename)
        print(f"Processing time: {time.time() - now:.3f}s")  # 记录并打印处理时间 


def on_new_frame_callback(frames: FrameSet, index: int):
    #这个函数是一个回调函数。
    # 当新的帧集（FrameSet）从某个数据流设备接收到时，会被调用。
    # 它接收两个参数：frames（一个FrameSet对象，代表新接收到的帧集）和index（一个整数，表示设备的索引）。
    global frames_queue
    global MAX_QUEUE_SIZE
    assert index < MAX_DEVICES  # 确保索引不超过最大设备数
    with frames_queue_lock: # 使用锁来确保线程安全，确保在修改frames_queue时不会发生线程冲突。
        if frames_queue[index].qsize() >= MAX_QUEUE_SIZE:  # 检查当前队列大小，如果队列已满，移除最旧的帧
            frames_queue[index].get()
        frames_queue[index].put(frames)  # 将新帧添加到队列中


def start_streams(pipelines: List[Pipeline], configs: List[Config]):
    index = 0
    for pipeline, config in zip(pipelines, configs):  #遍历pipelines和configs列表，将它们一一对应起来。
        print(f"Starting device {index}")  #打印当前正在启动的设备索引。
        pipeline.start(  #启动数据流设备，并传入配置和一个回调函数。
            config,  #启动数据流设备所需的所有配置信息
            lambda frame_set, curr_index=index: on_new_frame_callback(
                frame_set, curr_index
            ),  #这是一个匿名函数（也称为lambda函数），它将在数据流设备产生新帧时被调用。这个回调函数接收两个参数：frame_set和curr_index。
        )
        pipeline.enable_frame_sync()  #启用帧同步，确保来自不同设备的帧在时间上是同步的。
        index += 1  #增加设备索引，以便为下一个设备启动做准备。


def stop_streams(pipelines: List[Pipeline]):
    index = 0  # 初始化一个索引变量，用于在输出时标识设备
    for pipeline in pipelines:  # 遍历传入的pipeline列表
        print(f"Stopping device {index}")  # 打印当前正在停止的设备的索引
        pipeline.stop()  # 调用pipeline的stop方法来停止数据流
        index += 1 # 更新索引，以便为下一个设备打印正确的索引


# Main function for setup and teardown  设置和拆卸
def main():
    global curr_device_cnt  # 声明全局变量curr_device_cnt
    read_config(config_file_path)  # 调用read_config函数读取配置文件
    ctx = Context()  # 创建一个Context类的实例
    #"Context" 类通常是在编程中根据具体需求自定义的一个类，用于封装和管理与上下文（context）相关的数据和行为。
    
    device_0 = ctx.create_net_device("192.168.1.11", 8090)
    device_1 = ctx.create_net_device("192.168.1.12", 8090)
    device_2 = ctx.create_net_device("192.168.1.15", 8090)
    device_3 = ctx.create_net_device("192.168.1.16", 8090)
    device_list = [device_0,device_1,device_2,device_3]
    #device_list = ctx.query_devices() # 调用Context实例的query_devices方法来查询连接的设备列表
    #if device_list.get_count() == 0:  # 如果没有设备连接，则打印消息并返回
    if curr_device_cnt == 0:
        print("No device connected")
        return
    pipelines = []  # 初始化一个空列表，用于存储Pipeline实例  
    configs = []
    #curr_device_cnt = device_list.get_count()  # 将设备数量赋值给全局变量curr_device_cnt
    #for i in range(min(device_list.get_count(), MAX_DEVICES)):# 循环遍历设备列表，但不超过MAX_DEVICES个设备
    #for i in device_list:
    for i in range(len(device_list)):  
        #device = device_list.get_device_by_index(i)  # 根据索引获取设备
        device = device_list[i]
        pipeline = Pipeline(device)    # 为每个设备创建一个Pipeline对象
        config = Config()   # 创建一个Config对象来配置Pipeline
        serial_number = device.get_device_info().get_serial_number()  # 获取设备的序列号
        sync_config_json = multi_device_sync_config[serial_number]  # 从某个配置字典中根据序列号获取该设备的同步配置
        sync_config = device.get_multi_device_sync_config()  # 获取设备的当前同步配置
        sync_config.mode = sync_mode_from_str(sync_config_json["config"]["mode"])   # 根据JSON配置更新同步配置的各个字段
        sync_config.color_delay_us = sync_config_json["config"]["color_delay_us"]
        sync_config.depth_delay_us = sync_config_json["config"]["depth_delay_us"]
        sync_config.trigger_out_enable = sync_config_json["config"]["trigger_out_enable"]
        sync_config.trigger_out_delay_us = sync_config_json["config"]["trigger_out_delay_us"]
        sync_config.frames_per_trigger = sync_config_json["config"]["frames_per_trigger"]
        device.set_multi_device_sync_config(sync_config)   # 将更新后的同步配置设置回设备 
        print(f"Device {serial_number} sync config: {sync_config}")   # 打印设备的同步配置信息
           # 为Pipeline配置彩色传感器流 
        color_profile_list = pipeline.get_stream_profile_list(OBSensorType.COLOR_SENSOR)
        color_profile = color_profile_list.get_default_video_stream_profile()
        config.enable_stream(color_profile)
        has_color_sensor = True
        print(f"Device {serial_number} color profile: {color_profile}")
            # 为Pipeline配置深度传感器流 
        depth_profile_list = pipeline.get_stream_profile_list(OBSensorType.DEPTH_SENSOR)
        depth_profile = depth_profile_list.get_default_video_stream_profile()
        print(f"Device {serial_number} depth profile: {depth_profile}")
        config.enable_stream(depth_profile)
            # 将配置好的Pipeline和Config对象添加到列表中，以便后续处理 
        pipelines.append(pipeline)
        configs.append(config)
    start_streams(pipelines, configs)   #启动所有Pipeline的流
    global stop_processing# 定义一个全局变量来控制是否停止处理 
    try:
        process_frames(pipelines)  #处理从Pipeline中获取的帧
    except KeyboardInterrupt:
        print("Interrupted by user")
        stop_processing = True
    finally:# 无论是否发生异常，都停止所有Pipeline的流  
        print("===============Stopping pipelines====")
        stop_streams(pipelines)

# 如果此脚本作为主程序运行，则调用main()函数  
if __name__ == "__main__":
    main()
