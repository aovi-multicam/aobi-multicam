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
import cv2
import numpy as np

from pyorbbecsdk import *

ESC_KEY = 27


def main():
    pipeline = Pipeline()#创建pipeline对象，用于处理图像流
    config = Config()#创建xonfig对象，用于配置图像流
    # enable depth stream
    try:#获取深度数据流配置列表
        profile_list = pipeline.get_stream_profile_list(OBSensorType.DEPTH_SENSOR)
        if profile_list is None:
            print("No depth sensor found")
            return
        profile = profile_list.get_default_video_stream_profile()#获取默认的视频流设置
        config.enable_stream(profile)#启用深度流
    except Exception as e:
        print(e)
        return
    # enable color stream
    try:#获取彩色数据流配置列表
        profile_list = pipeline.get_stream_profile_list(OBSensorType.COLOR_SENSOR)
        if profile_list is None:
            print("No color sensor found")
            return
        profile = profile_list.get_default_video_stream_profile()
        config.enable_stream(profile)#启用彩色流
    except Exception as e:
        print(e)

    pipeline.start(config)#启用图像流处理
    pipeline.start_recording("./test.bag")#开始录制到文件“./test.bag"
    while True:
        try:
            frames = pipeline.wait_for_frames(100)#等待获取帧
            if frames is None:
                continue
            depth_frame = frames.get_depth_frame()
            if depth_frame is None:
                continue
            width = depth_frame.get_width()#获取深度帧宽度
            height = depth_frame.get_height()#获取深度帧高度
            scale = depth_frame.get_depth_scale()#获取深度帧深度比例
            #深度数据处理
            depth_data = np.frombuffer(depth_frame.get_data(), dtype=np.uint16)#从深度帧数据中获取深度数据
            depth_data = depth_data.reshape((height, width))#将深度数据整形为二维数组
            depth_data = depth_data.astype(np.float32) * scale#深度数据*深度比例_rescale
            depth_image = cv2.normalize(depth_data, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)#将深度数据标准化
            depth_image = cv2.applyColorMap(depth_image, cv2.COLORMAP_JET)#颜色映射生成深度图像
            cv2.imshow("Depth Viewer", depth_image)#opencv2显示深度图像
            key = cv2.waitKey(1)#等待键盘输入，1ms超时
            if key == ord('q') or key == ESC_KEY:
                pipeline.stop_recording()
                break
        except KeyboardInterrupt:
            pipeline.stop_recording()
            break
    pipeline.stop()


if __name__ == "__main__":
    main()
