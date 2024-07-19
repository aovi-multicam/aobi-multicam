# ******************************************************************************
#  Copyright (c) 2023 Orbbec 3D Technology, Inc
#  
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.  
#  You may obtain a copy of the License at
#  
#      http:# www.apache.org/licenses/LICENSE-2.0
#  
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
# ******************************************************************************
from queue import Queue
from typing import List

import cv2
import numpy as np

from pyorbbecsdk import *
from utils import frame_to_bgr_image

MAX_DEVICES = 2 # 最大设备数
curr_device_cnt = 2  # 目前设备数

MAX_QUEUE_SIZE = 5 # 最大帧队列数
ESC_KEY = 27 # 退出按键ascii码
 
# 为每个设备创建一个队列对象
color_frames_queue: List[Queue] = [Queue() for _ in range(MAX_DEVICES)]
depth_frames_queue: List[Queue] = [Queue() for _ in range(MAX_DEVICES)]
has_color_sensor: List[bool] = [False for _ in range(MAX_DEVICES)]
stop_rendering = False

# 获取新帧的回调函数
def on_new_frame_callback(frames: FrameSet, index: int):
    global color_frames_queue, depth_frames_queue
    global MAX_QUEUE_SIZE
    assert index < MAX_DEVICES
    color_frame = frames.get_color_frame() # 获取RGB帧
    depth_frame = frames.get_depth_frame() # 获取深度帧
    if color_frame is not None:
        # 如果队列中的帧数大于最大队列大小，则从队列中删除帧
        if color_frames_queue[index].qsize() >= MAX_QUEUE_SIZE:
            color_frames_queue[index].get() 
        color_frames_queue[index].put(color_frame) # 将RGB帧放入队列
    if depth_frame is not None:
        if depth_frames_queue[index].qsize() >= MAX_QUEUE_SIZE:
            depth_frames_queue[index].get()
        depth_frames_queue[index].put(depth_frame)


# 渲染帧
# 目的 :它的目的是从两个全局队列 color_frames_queue 和 depth_frames_queue 中获取彩色和深度帧，并将它们渲染到窗口中。
# 该函数在一个无限循环中运行，直到 stop_rendering 变量为 True 为止。在每次迭代中，它检查每个设备的队列是否为空。


def rendering_frames():
    global color_frames_queue, depth_frames_queue
    global curr_device_cnt
    global stop_rendering
    while not stop_rendering:
        for i in range(curr_device_cnt):
            color_frame = None # RGB帧初始化
            depth_frame = None # 深度帧初始化
            if not color_frames_queue[i].empty(): # 如果RGB队列不为空 获取RGB帧
                color_frame = color_frames_queue[i].get() # 
            if not depth_frames_queue[i].empty(): # 如果深度队列不为空 获取深度帧
                depth_frame = depth_frames_queue[i].get() # 
            if color_frame is None and depth_frame is None: # 如果RGB和深度帧都为空 跳过本次循环
                continue # 
            color_image = None # RGB图像初始化
            depth_image = None # 深度图像初始化
            color_width, color_height = 0, 0 # RGB宽高初始化
            if color_frame is not None: # 如果RGB帧不为空 获取RGB帧的宽高和图像 

                # RGB数据处理
                color_width, color_height = color_frame.get_width(), color_frame.get_height() # 获取RGB帧的宽高
                color_image = frame_to_bgr_image(color_frame) # 将RGB帧转换为BGR图像
            if depth_frame is not None: # 如果深度帧不为空
                width = depth_frame.get_width() # 获取深度帧的宽
                height = depth_frame.get_height() # 获取深度帧的高
                scale = depth_frame.get_depth_scale() # 获取深度帧的深度比例

                # 深度数据处理
                # 从深度帧中获取深度数据    
                depth_data = np.frombuffer(depth_frame.get_data(), dtype=np.uint16)
                # 将深度数据转换成长宽为 height 和 width 的数组
                depth_data = depth_data.reshape((height, width))
                # 将深度数据转换成浮点数并乘以深度比例
                depth_data = depth_data.astype(np.float32) * scale
                # 将深度数据转换成 8 位无符号整数 归一化到0-255
                depth_image = cv2.normalize(depth_data, None, 0, 255, cv2.NORM_MINMAX,
                                            dtype=cv2.CV_8U)
                # 将深度图像转换成伪彩色图像
                depth_image = cv2.applyColorMap(depth_image, cv2.COLORMAP_JET)

            if color_image is not None and depth_image is not None: 
                # 图像最终处理
                window_size = (color_width // 2, color_height // 2) 
                color_image = cv2.resize(color_image, window_size) 
                depth_image = cv2.resize(depth_image, window_size) 
                image = np.hstack((color_image, depth_image)) # 水平拼接RGB和深度图像
            elif depth_image is not None and not has_color_sensor[i]: 
                image = depth_image
            else:
                continue
            cv2.imshow("Device {}".format(i), image) # 显示图像
            key = cv2.waitKey(1)
            if key == ord('q') or key == ESC_KEY: 
                return

# 全部设备开启数据流
def start_streams(pipelines: List[Pipeline], configs: List[Config]):
    index = 0
    for pipeline, config in zip(pipelines, configs): # 遍历pipelines和configs列表中的元素
        print("Starting device {}".format(index))
        pipeline.start(config, lambda frame_set, curr_index=index: on_new_frame_callback(frame_set,
                                                                                         curr_index)) 
        # config是当前迭代的配置对象，而回调函数是当新的帧数据到达时将被调用的函数
        # curr_index=index 用于将当前设备的索引传递给回调函数
        # 当新的帧数据到达时，回调函数将被调用，并且将当前设备的索引作为参数传递给回调函数
        index += 1

# 全部设备停止数据流
def stop_streams(pipelines: List[Pipeline]):
    for pipeline in pipelines:
        pipeline.stop()


def main():
    ctx = Context() # Context对象
    device_0 = ctx.create_net_device("192.168.1.12", 8090)
    device_1 = ctx.create_net_device("192.168.1.16", 8090)
    #device_2 = ctx.create_net_device(192.168.1.12, 8090)

    device_list = [device_0, device_1]
    global curr_device_cnt
    #curr_device_cnt = device_list.get_count()
    if curr_device_cnt == 0:
        print("No device connected")
        return
    if curr_device_cnt > MAX_DEVICES:
        print("Too many devices connected")
        return
    pipelines: List[Pipeline] = []
    configs: List[Config] = []
    global has_color_sensor
    i = 0
    for device in device_list:
        # 创建一个pipeline对象,用于管理与给定设备 device 相关的数据流
        pipeline = Pipeline(device)
        # 创建一个 Config 对象，用于配置 orbbec 设备的数据流参数。
        config = Config()
        try:

            # 获取与RGB相关的流配置文件列表 获取的是RGB的视频流配置文件
            profile_list = pipeline.get_stream_profile_list(OBSensorType.COLOR_SENSOR)
            color_profile: VideoStreamProfile = profile_list.get_default_video_stream_profile()
            # 使能RGB流
            config.enable_stream(color_profile)
            has_color_sensor[i] = True

        except OBError as e: # 报错认为没有RGB
            print(e)
            has_color_sensor[i] = False
        
        # 获取与深度相关的流配置文件列表 获取的是深度的视频流配置文件
        profile_list = pipeline.get_stream_profile_list(OBSensorType.DEPTH_SENSOR)
        depth_profile = profile_list.get_default_video_stream_profile()
        # 使能深度流
        config.enable_stream(depth_profile)
        # 添加pipeline和config到对应列表
        pipelines.append(pipeline)
        configs.append(config)
        i += 1 # 设备索引加1

    global stop_rendering
    # 开启数据流
    start_streams(pipelines, configs)
    try:
        rendering_frames()
        stop_streams(pipelines)
    except KeyboardInterrupt:
        stop_rendering = True
        stop_streams(pipelines)


if __name__ == "__main__":
    main()
