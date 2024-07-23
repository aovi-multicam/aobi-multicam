# 多相机同步采集
基于RGBD相机的实时视频采集，建⽴实时的⼈体的数字信息采集。是当前⽐较热⻔的⼀个⾏业趋势，在AR/XR，运动检测、6G数字通信领域有⼴泛的需求。

本方案目的实现⼀套多相机的同步采集和拼接，解决体积视频中，多相机同步采集，点云拼接的⼯程问题，实现8台相机的实时点云采集；

本文档详细讲解了关于Orbbec Femto Mega相机的8相机同步采集方案，结构如下：


## 零件清单
本节详细叙述多相机同步方案所需部件：

|    物料清单   |         规格                 |用量   |    备注    |       
|----------------|-------------------------------|-----------------------------|-----------------------|
|FemtoMega|[FemtoMega规格说明](https://www.orbbec.com.cn/index/Megadoc/info.html?cate=118&id=58) |8台          |后期拓展20台|
|POE万兆交换机|[https://item.jd.com/100024907399.html](https://item.jd.com/100024907399.html)  |1台          |
|多级同步盒子 |[同步盒子规格](https://item.taobao.com/item.htm?spm=a1z10.5-c-s.w4002-16718678529.13.1e3d4700yIBmFV&id=758379921935)|1台|
|多机网线接口|[多级同步接口](https://item.taobao.com/item.htm?spm=a1z10.5-c-s.w4002-16718678529.13.1e3d4700yIBmFV&id=758379921935)|8台|
|多级同步网线|千兆网线|8台|
|采集电脑|支持2个千兆网卡|1台|
|千兆网线||2条|交换机和采集主机的连线|

## 方案框图

## 首次设置
本节将介绍使用FemtoMega相机的首次设置

### 更新固件
本方案中，需确保所使用相机固件均已更新到最新版本。阅读[Orbbec说明](https://www.orbbec.com/products/)，可对FemtoMega设备上固件进行更新。

### Windows特定设置
对于 Windows 上的图像元数据支持，每个相机必须至少与 Orbbec Viewer 使用一次。如果使用 Orbbec Viewer 更新所有相机上的固件，则此操作将自动发生，无需采取进一步操作。

但是，如果在新 PC 上使用摄像机而未在此 PC 上更新其固件，则请在这台 PC 上使用每个摄像机与 Orbbec Viewer 一次，以完成此设置步骤，然后再将它们与 ScannedReality Studio 一起使用。

## 配置环境
本节将介绍

### 所需软件
* **Anaconda** ：https://www.anaconda.com/
* **Vscode** : https://code.visualstudio.com/
* **pyorbbecSDK** : https://github.com/orbbec/pyorbbecsdk
* **Cmake** : https://cmake.org/download/

### 配置步骤
1. 获取Python 3.11：
Anaconda可以创建虚拟环境达成。打开anaconda prompt，输入命令​```conda create -n aobi_multicam python=3.11
​```，创建Python 3.11 的环境。安装在Vscode中就可以使用虚拟环境的Python了。
2. 获取pyorbbecSDK
3. 安装依赖：进入sdk，在命令行输入```pip install -r.\requirements.txt```
4. 在Cmake中build整个工程：
在Vscode中下载Cmake插件，安装完成后右键CmakeLists,txt 就可以去 build all Projects[tupian]
5. 重新编译整个pyorbbecSDK
如果遇到下列情况一般是 Pybind11 的位置没有找到，在 CmakeList.txt 中加入即可[tupian]
在下图文件夹中用 Vscode 打开 pyorbbecsdk.sln[tupian]，点击INSTALL，生成[tupian]，将在 install/lib/ 中生成四个库文件
6. 将install文件夹的动态库加入工程目录（也可尝试放入examples文件夹中），接入 OrbbecSDK 的深度相机运行depth_viewer.py ，结果如下图，即可认为环境配置成功。
图片[de]（effect） 

## FemtoMega组网
本节将介绍FemtoMega组网过程，步骤如下：

1. 确认采集电脑是否处于同一以太网内。若不是，需对采集电脑进行手动IP设置。
2. 连接FemtoMega：将FemtoMega网线接到有POE的设备上，通过网线供电和传输数据。
3. 检查是否连接成功：打开**最新版OrbeecViewer**，若出现如下信息时，即为连接成功。
4. 更改相机IP：在OrbbecViewer——相机控制——IP配置中，对Mega的网络IP进行手动控制。

## 多相机同步
本节将介绍
### 相机配置文件
在SDK文件中程序文件内：\pyorbbecsdk\pyorbbecsdk\config，找到配置文件："multi_device_sync_config.json"，按照下图进行配置，配置完成进行保存。

### 连接设备
在**星型配置**中连接 Femto Mega 设备：
1. 将每台Femto Mega 连接到电源。
2. 将每台设备连接到其自身的电脑主机。
3. 选择一台设备充当主设备，并将同步线与主设备连接上。
4. 将该同步转接线的另一端接入T568B to T568B的网线，网线另一端接入专业版星型同步集线器的Primary In接口。
5. 若要连接另一个设备，请将同步线与Femto Mega 同步接口连接上，并用网线连接到同步线另一端，网线的另一端连接同步集线器的第一个从属设备接口：Secondary Cam 1。第二个从属设备连接Secondary Cam 2  ，以此类推。
6. 重复上述步骤，直到所有设备都已连接。
