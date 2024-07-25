# 多相机同步采集
基于RGBD相机的实时视频采集，建⽴实时的⼈体的数字信息采集。是当前⽐较热⻔的⼀个⾏业趋势，在AR/XR，运动检测、6G数字通信领域有⼴泛的需求。

本方案目的实现⼀套多相机的同步采集和拼接，解决体积视频中，多相机同步采集，点云拼接的⼯程问题，实现8台相机的实时点云采集；

本文档详细讲解了关于Orbbec Femto Mega相机的8相机同步采集方案，结构如下：

前两节概述了本方案所需零件清单摘要与方案拓扑图：
* **零件清单**
* **方案框图**

接下来部分介绍了使用 Femto Mega 相机时首次设置与环境配置的步骤：
* **首次设置**
* **环境配置**

然后，我们详细介绍了该方案的同步，标定，及点云图拼接：
* **多相机同步**
* **相机标定**
* **点云图拼接**

文档页面最后解答了部分故障排除及总结了目前方案仍面临的问题：
* **故障排除**
* **遇到问题**

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
![connectiondiagram](\picture\connectiondiagram.png)

实际环境图：
![praticaldiagram](picture\IMG_7320.HEIC)
## 首次设置
本节将介绍使用FemtoMega相机的首次设置：

### 更新固件
本方案中，需确保所使用相机固件均已更新到最新版本。阅读[Orbbec说明](https://www.orbbec.com/products/)，可对FemtoMega设备上固件进行更新。

### Windows特定设置
对于 Windows 上的图像元数据支持，每个相机必须至少与 Orbbec Viewer 使用一次。如果使用 Orbbec Viewer 更新所有相机上的固件，则此操作将自动发生，无需采取进一步操作。

但是，如果在新 PC 上使用摄像机而未在此 PC 上更新其固件，则请在这台 PC 上使用每个摄像机与 Orbbec Viewer 一次，以完成此设置步骤，然后再将它们与 ScannedReality Studio 一起使用。

## 配置环境
本节将介绍相机使用所需环境：

### 所需软件
* **Anaconda** ：https://www.anaconda.com/
* **Vscode** : https://code.visualstudio.com/
* **pyorbbecSDK** : https://github.com/orbbec/pyorbbecsdk
* **Cmake** : https://cmake.org/download/
* **Matlab** ：https://www.mathworks.com/

### 配置步骤
1. 获取Python 3.11：
Anaconda可以创建虚拟环境达成。打开anaconda prompt，输入命令​```conda create -n aobi_multicam python=3.11
​```，创建Python 3.11 的环境。安装在Vscode中就可以使用虚拟环境的Python了。
2. 获取pyorbbecSDK
3. 安装依赖：进入sdk，在命令行输入```pip install -r.\requirements.txt```
4. 在Cmake中build整个工程：
在Vscode中下载Cmake插件，安装完成后右键CmakeLists,txt 就可以去 build all Projects
![pcrequire1](\picture\PCrequirements\pcrequire1.png)
5. 重新编译整个pyorbbecSDK
如果遇到下列情况一般是 Pybind11 的位置没有找到，在 CmakeList.txt 中加入即可
![pcrequire2](\picture\PCrequirements\pcrequire2.png)![pcrequire3](\picture\PCrequirements\pcrequire3.png)
在下图文件夹中用 Vscode 打开 pyorbbecsdk.sln!![pcrequire4](\picture\PCrequirements\pcrequire4.png)
点击INSTALL，生成![pcrequire5](\picture\PCrequirements\pcrequire5.png)
将在 install/lib/ 中生成四个库文件
![pcrequire6](\picture\PCrequirements\pcrequire6.png)
6. 将install文件夹的动态库加入工程目录（也可尝试放入examples文件夹中），接入 OrbbecSDK 的深度相机运行 depth_viewer.py ，结果如下图，即可认为环境配置成功。
![pcrequire7](\picture\PCrequirements\pcrequire7.png)

## FemtoMega组网
本节将介绍FemtoMega组网过程，步骤如下：

1. 确认采集电脑是否处于同一以太网内。若不是，需对采集电脑进行手动IP设置。
![ipsetup1](\picture\ipnet\net3.png)
2. 连接 Femto Mega ：将 Femto Mega 网线接到有POE的设备上，通过网线供电和传输数据。
3. 检查是否连接成功：打开**最新版OrbeecViewer**，若出现如下信息时，即为连接成功。
![ipsetup2](\picture\ipnet\net1.png)
4. 更改相机IP：在OrbbecViewer——相机控制——IP配置中，对Mega的网络IP进行手动控制。
![ipsetup3](\picture\ipnet\net2.png)

## 多相机同步
本节将介绍多相机同步步骤：
### 相机配置文件
在SDK文件中程序文件内：\pyorbbecsdk\pyorbbecsdk\config，找到配置文件："multi_device_sync_config.json"，按照下图进行配置，配置完成进行保存。
![jsonsetup](\picture\multisync\jsonsetup.png)
### 连接设备
在**星型配置**中连接 Femto Mega 设备：
1. 将每台Femto Mega 连接到电源。
2. 将每台设备连接到其自身的电脑主机。
3. 选择一台设备充当主设备，并将同步线与主设备连接上。
4. 将该同步转接线的另一端接入T568B to T568B的网线，网线另一端接入专业版星型同步集线器的Primary In接口。
5. 若要连接另一个设备，请将同步线与Femto Mega 同步接口连接上，并用网线连接到同步线另一端，网线的另一端连接同步集线器的第一个从属设备接口：Secondary Cam 1。第二个从属设备连接Secondary Cam 2  ，以此类推。
6. 重复上述步骤，直到所有设备都已连接。
### 运行多机同步
1. 在 Vscode 中打开 eight_net_devices_sync.py 程序，点击运行。
2. 开流成功后预览多机效果图如下：
![multidevice_effect_sketch](\picture\multisync\multidevice_effect_sketch.png)
3. 验证多机同步：观察时间戳（当多机时间戳基本相同时即可证明多机同步）
![multidevice_effect_sketch](\picture\multisync\timestamp.png)
## 相机标定
本节将介绍张正友标定法对相机外参,与 Matlab 工具箱对相机内外参进行标定：
### 张正友标定法
1. 对单相机进行标定，得到两个相机的外参。
2. 对两组外参通过世界坐标系转换，从而将两个相机的像素坐标行进行转换，最终得到两个相机之间的坐标系转换。
![connect_principle](\picture\pointcloud_connect\pcc1.png)
由于本方案中使用的相机均为 Femto Mega ，因此方案中将相机内参近似相同。
### Matlab Computer vision toolbox
1. 在 Matlab中下载 Computer vision toolbox。
2. 采集相机照片：双机采集一组照片，过程中需注意保持相机与标定板不动，且尽量让标定板以不同的姿态铺满 RGB 照片，姿态尽量丰富。
3. 使用 Stereo camera calibrator 进行标定。
4. 可以在优化选项中输入相机初始内参，使用 Orbbec viewer 可以查看内参，运行后再在命令行中可打印内外参。

## 点云图拼接
本节将介绍点云图拼接的原理及拼接步骤：
1. 从8台Femto Mega相机拿取数据，用open3d库提取点云数据，加载到点云列表进行逐个拼接
2. 对点云列表的数据做采样，降低点云数据量（本方案中采集主机为Lenove R5-5800H）
3. 采用icp算法对点云进行对齐，对点云进行拼接
4. 输出可视化结果，并将拼接后点云进行保存

## 故障排除
**Q:** Cmake K4A_SDK 报错，显示缺少库文件

**A:** 需要将源码 gitclone 后进行 gitmodule ，检查缺少的库文件并进行添加

**Q:** 电脑已开代理，但 gitmododule 过程中一直处于报错状态 failed

**A:** 命令行需要单独开代理```set http_proxy=http://127.0.0.1:7890 & set https_proxy=http://127.0.0.1:7890```，命令行可参考以上命令进行设置，其中7890为采集电脑的代理端口号

**Q:** 当使用 viewer 开启视频时设备闪烁黄灯且无法打开视频
![Wrongcondition](\picture\QandA\Q1.png)

**A:** 同步时该设备被设置为从机，在 viewer 中修改为主机即可正常使用

**Q:** 运行 K4A_SDK 中的 green_screen 的双机模式时报错没有同步
![multimodenotsync](\picture\QandA\Q2.png)

**A:** 在 viewer 中设置主从机即可

**Q:** 程序报错，显示缺少 DDL 文件
![lackofddl](\picture\QandA\Q3.png)

**A:** 可在文件编辑器中搜索相关文件并添加到目录中即可

**Q:** viewer 可以检测到网络连接的设备，但点击链接后无法链接

**A:** 需要手动设置电脑IP

**Q:** 手动配置网络后出现连接失败

**A:** 在同一网络中，多台电脑设置了同一 IP

## 遇到问题
本节将介绍在Femto Mega多相机同步采集中所遇到的问题：
### 多台设备网线连接存在掉帧
由于网络连接的本身的传输的问题，本方案在接收8台Femto Mega的数据流的时候会导致掉帧，从而影响动态场景的显示。
### 点云处理时间
本方案中所使用的 pointcloud.py，受处理电脑算力影响，点云处理时间较长。同时不同相机间存在色差区别，因此拼接后效果图存在严重的灰度值断层
### 软件标定误差
在相机拍摄图片进行标定时，存在轻微抖动，无法做到完全固定，引起较大的标定误差，从而导致点云对齐问题较难解决